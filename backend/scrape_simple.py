"""
Simplified scraper - Uses Apify Yellow Pages Actor (Enhanced v2.7)
2026 穩定版 - 整合 Email 撈取、進階去重與 全域隔離池 (Global Lead Pool) 同步
"""

import os
import time
import models
from database import SessionLocal
from logger import add_log, add_task_log
from urllib.parse import urlparse
from datetime import datetime
from scrape_utils import sync_from_global_pool, save_to_global_pool
import ai_service

# Apify 整合
try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False


def extract_domain(url: str) -> str:
    """從 URL 萃取 Domain"""
    if not url: return ""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain.lower().strip()
    except:
        return ""


def scrape_simple(market: str = "US", pages: int = 3, keywords: list = None, user_id: int = None):
    """
    使用黃頁模式 (Apify) 探勘公司。
    v2.7：先從全域池同步，不足時才進行爬取，並將新結果同步回全域池。
    """
    if keywords is None:
        keywords = ["manufacturer"]
    
    db = SessionLocal()
    from config_utils import get_general_setting
    sync_enabled = get_general_setting(db, "enable_global_sync", default=True, user_id=user_id)
    
    # 建立任務記錄
    task_record = models.ScrapeTask(
        user_id=user_id,
        market=market,
        keywords=",".join(keywords) if keywords else "manufacturer",
        miner_mode="yellowpages",
        pages_requested=pages,
        status="Running"
    )
    db.add(task_record)
    db.commit()
    db.refresh(task_record)
    task_id = task_record.id

    stats = {"saved": 0, "synced": 0, "skipped": 0, "errors": 0}
    
    add_log(f"🔍 [Apify 爬蟲] 開始任務 #{task_id}")
    add_task_log(db, task_id, "info", f"任務啟動 | 市場: {market} | 關鍵字: {keywords}")
    
    if not APIFY_AVAILABLE:
        add_task_log(db, task_id, "error", "apify-client 未安裝")
        return stats
    
    try:
        for ki, keyword in enumerate(keywords):
            add_log(f"📌 正在爬取關鍵字 ({ki+1}/{len(keywords)}): {keyword}")
            add_task_log(db, task_id, "info", f"開始處理關鍵字: {keyword}", keyword=keyword)
            
            for page in range(1, pages + 1):
                try:
                    results = scrape_keyword_page_apify(keyword, page, market, db, task_id, user_id)
                    
                    for item in results:
                        name = item.get("name", "").strip()
                        website = item.get("url", "").strip()
                        domain = extract_domain(website)
                        
                        if not name: continue

                        # ─── v2.7.1: 全域隔離池同步邏輯 (考慮 sync_enabled) ───
                        lead_obj, is_synced = sync_from_global_pool(db, user_id, domain, name, sync_enabled=sync_enabled)
                        
                        if lead_obj and not is_synced:
                            # 代表私有清單原本就有這家公司 (既存重複)
                            stats["skipped"] += 1
                            continue
                        
                        if is_synced:
                            # 代表從全域池成功同步了一筆 (節省了存儲與分類成本)
                            stats["synced"] += 1
                            continue
                        
                        # ─── 執行到此代表是全新的名單 (Live Scrape Result) ───
                        
                        # 1. AI 產業別標籤 (使用 v2.7 新版分類器)
                        description = item.get("description", "") or "Business listing from Yellowpages"
                        ai_result = ai_service.analyze_company_and_tag(name, description, use_gpt=False, db=db, user_id=user_id)
                        
                        # 2. Email 處理
                        raw_emails = item.get("email") or item.get("emails") or item.get("contactEmail") or []
                        if isinstance(raw_emails, str): candidate_list = [raw_emails]
                        elif isinstance(raw_emails, list): candidate_list = raw_emails
                        else: candidate_list = []
                        
                        primary_email = candidate_list[0] if candidate_list else ""
                        email_candidates_str = ", ".join(candidate_list) if candidate_list else ""

                        # 3. 儲存私有 Lead
                        new_lead = models.Lead(
                            user_id=user_id,
                            company_name=name,
                            website_url=website,
                            domain=domain,
                            description=description,
                            phone=item.get("phone", ""),
                            address=item.get("address", ""),
                            contact_email=primary_email,
                            email_candidates=email_candidates_str,
                            ai_tag=ai_result.get("Tag", "AUTO-YELLOWPAGES"),
                            status="Scraped",
                            scrape_location=market,
                            extracted_keywords=keyword,
                            assigned_bd=ai_result.get("BD", "General")
                        )
                        db.add(new_lead)
                        db.commit()
                        db.refresh(new_lead)
                        stats["saved"] += 1
                        
                        # 4. 同步回全域池 (Isolation Table)
                        save_to_global_pool(db, {
                            "company_name": name,
                            "domain": domain,
                            "website_url": website,
                            "description": description,
                            "contact_email": primary_email,
                            "email_candidates": email_candidates_str,
                            "phone": item.get("phone", ""),
                            "address": item.get("address", ""),
                            "ai_tag": ai_result.get("Tag"),
                            "source": "apify_yellowpages"
                        })
                        # 連結 global_id
                        global_rec = db.query(models.GlobalLead).filter(models.GlobalLead.domain == domain).first()
                        if global_rec:
                            new_lead.global_id = global_rec.id
                            db.commit()
                    
                    add_task_log(
                        db, task_id, "success",
                        f"頁面 {page} 完成 | 新增 {stats['saved']} | 同步 {stats['synced']} | 跳過 {stats['skipped']}",
                        keyword=keyword, page=page
                    )
                    
                    time.sleep(1)
                    
                except Exception as e:
                    stats["errors"] += 1
                    add_log(f"❌ 關鍵字 {keyword} 出錯: {str(e)}")
        
        # 任務結束更新
        task_record.status = "Completed"
        task_record.leads_found = stats["saved"] + stats["synced"]
        task_record.completed_at = datetime.utcnow()
        db.commit()
        
        summary = f"完成 | 新增:{stats['saved']} 同步:{stats['synced']} 跳過:{stats['skipped']} 錯誤:{stats['errors']}"
        add_log(f"🏁 [任務 #{task_id}] {summary}")
        add_task_log(db, task_id, "success", summary)
        return stats
        
    except Exception as e:
        task_record.status = "Failed"
        task_record.error_message = str(e)[:500]
        db.commit()
        raise
    finally:
        db.close()


def scrape_keyword_page_apify(keyword: str, page: int, market: str = "US", db=None, task_id: int = None, user_id: int = None) -> list:
    """核心爬取函式：調用 Apify Actor"""
    from config_utils import get_api_key
    api_token = get_api_key(db, "apify", user_id)
    if not api_token: return []
    
    client = ApifyClient(api_token)
    location_map = {"US": "United States", "UK": "United Kingdom", "CA": "Canada", "AU": "Australia"}
    location = location_map.get(market, market)
    
    # 支援新版 Actor (junipr)
    actor_id = "junipr/yellow-pages-scraper"
    run_input = {
        "searchTerms": [keyword],
        "location": location,
        "maxResults": 20,
        "extractEmails": True,
        "includeDetails": True
    }
    
    try:
        add_log(f"🌐 [Apify] 呼叫 Actor: {actor_id} | 頁面: {page}")
        run = client.actor(actor_id).call(run_input=run_input)
        
        if not run or not run.get("defaultDatasetId"):
            # 備援
            run = client.actor("automation-lab/yellowpages-scraper").call(run_input={
                "searchTerms": keyword, "location": location, "maxResults": 20
            })

        if not run or not run.get("defaultDatasetId"): return []
            
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        results = []
        for item in items:
            results.append({
                "name": item.get("businessName") or item.get("name", ""),
                "url": item.get("website") or item.get("url", ""),
                "phone": item.get("phone", ""),
                "description": item.get("description", ""),
                "address": item.get("address", "") or item.get("street", ""),
                "email": item.get("email"),
                "emails": item.get("emails"),
                "contactEmail": item.get("contactEmail")
            })
        return results
    except Exception as e:
        add_log(f"❌ Apify API 失敗: {str(e)}")
        return []

if __name__ == "__main__":
    scrape_simple("US", 1, ["metal factory"])
