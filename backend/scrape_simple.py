"""
Simplified scraper - Uses Apify Yellow Pages Actor (Enhanced v2.6)
2026 穩定版 - 整合 Email 撈取與進階去重邏輯
"""

import os
import time
import models
from database import SessionLocal
from logger import add_log, add_task_log
from urllib.parse import urlparse
from datetime import datetime

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
    使用黃頁模式 (Apify) 探勘公司，並自動撈取 Email 與執行進階去重。
    """
    if keywords is None:
        keywords = ["manufacturer"]
    
    db = SessionLocal()
    
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

    stats = {"saved": 0, "skipped": 0, "errors": 0}
    
    add_log(f"🔍 [Apify 爬蟲] 開始任務 #{task_id}")
    add_task_log(db, task_id, "info", f"任務啟動 | 市場: {market} | 關鍵字: {keywords}")
    
    if not APIFY_AVAILABLE:
        add_task_log(db, task_id, "error", "apify-client 未安裝")
        return stats
    
    try:
        for ki, keyword in enumerate(keywords):
            add_log(f"📌 正在爬取關鍵字 ({ki+1}/{len(keywords)}): {keyword}")
            add_task_log(db, task_id, "info", f"開始爬取關鍵字: {keyword}", keyword=keyword)
            
            for page in range(1, pages + 1):
                try:
                    results = scrape_keyword_page_apify(keyword, page, market, db, task_id, user_id)
                    
                    for item in results:
                        name = item.get("name", "").strip()
                        website = item.get("url", "").strip()
                        domain = extract_domain(website)
                        
                        if not name: continue
                        
                        # ─── 進階去重邏輯 (Domain 優先 -> 名稱) ───
                        existing = None
                        if domain:
                            existing = db.query(models.Lead).filter(
                                models.Lead.domain == domain,
                                models.Lead.user_id == user_id
                            ).first()
                        
                        if not existing:
                            existing = db.query(models.Lead).filter(
                                models.Lead.company_name == name,
                                models.Lead.user_id == user_id
                            ).first()
                        
                        if existing:
                            stats["skipped"] += 1
                            continue
                        
                        # ─── Email 處理 ───
                        # 支援多個 Key：email, emails, contactEmail
                        raw_emails = item.get("email") or item.get("emails") or item.get("contactEmail") or []
                        
                        # 轉換為列表
                        if isinstance(raw_emails, str):
                            candidate_list = [raw_emails]
                        elif isinstance(raw_emails, list):
                            candidate_list = raw_emails
                        else:
                            candidate_list = []
                            
                        # 取第一個作為主要 email
                        primary_email = candidate_list[0] if candidate_list else ""
                        email_candidates_str = ", ".join(candidate_list) if candidate_list else ""

                        # 儲存 Lead
                        lead = models.Lead(
                            user_id=user_id,
                            company_name=name,
                            website_url=website,
                            domain=domain,
                            phone=item.get("phone", ""),
                            address=item.get("address", ""),
                            contact_email=primary_email,
                            email_candidates=email_candidates_str,
                            ai_tag="AUTO-YELLOWPAGES",
                            status="Scraped",
                            scrape_location=market,
                            extracted_keywords=keyword
                        )
                        db.add(lead)
                        db.commit()
                        stats["saved"] += 1
                    
                    add_task_log(
                        db, task_id, "success",
                        f"頁面 {page} 完成 | 取得 {len(results)} 筆 | 本次新增 {stats['saved']}",
                        keyword=keyword, page=page
                    )
                    
                    # 避免 API 頻率過高
                    time.sleep(1)
                    
                except Exception as e:
                    stats["errors"] += 1
                    add_log(f"❌ 關鍵字 {keyword} 第 {page} 頁出錯: {str(e)}")
        
        # 任務結束更新
        task_record.status = "Completed"
        task_record.leads_found = stats["saved"]
        task_record.completed_at = datetime.utcnow()
        db.commit()
        
        summary = f"完成 | 新增:{stats['saved']} 跳過:{stats['skipped']} 錯誤:{stats['errors']}"
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
    """
    核心爬取函式：優先使用 junipr/yellow-pages-scraper 進行深層 Email 提取
    """
    from config_utils import get_api_key
    api_token = get_api_key(db, "apify", user_id)
    
    if not api_token:
        add_log("⚠️ Apify API Key 缺失")
        return []
    
    client = ApifyClient(api_token)
    
    # 地點對照
    location_map = {
        "US": "United States",
        "UK": "United Kingdom",
        "CA": "Canada",
        "AU": "Australia"
    }
    location = location_map.get(market, market)
    
    # ─── Apify Actor 參數設定 ───
    # 使用 junipr/yellow-pages-scraper 以獲得更好的 Email 提取率
    actor_id = "junipr/yellow-pages-scraper"
    run_input = {
        "searchTerms": [keyword],
        "location": location,
        "maxResults": 20, # 每頁建議不超過 20 筆以確保效能
        "extractEmails": True, # 加強版 Email 提取
        "includeDetails": True # 進入詳細頁面
    }
    
    try:
        add_log(f"🌐 [Apify] 呼叫 Actor: {actor_id} | 關鍵字: {keyword}")
        
        run = client.actor(actor_id).call(run_input=run_input)
        
        if not run or not run.get("defaultDatasetId"):
            add_log("⚠️ Actor 回傳無資料，嘗試備援 Actor...")
            # 備援使用 automation-lab
            run = client.actor("automation-lab/yellowpages-scraper").call(run_input={
                "searchTerms": keyword,
                "location": location,
                "maxResults": 20
            })

        if not run or not run.get("defaultDatasetId"):
            return []
            
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        results = []
        for item in items:
            # 地址處理
            address = item.get("address", "") or " ".join(filter(None, [
                item.get('street', ''), item.get('city', ''), item.get('state', '')
            ]))
            
            results.append({
                "name": item.get("businessName") or item.get("name", ""),
                "url": item.get("website") or item.get("url", ""),
                "phone": item.get("phone", ""),
                "address": address,
                # 傳遞所有可能的 email 欄位
                "email": item.get("email"),
                "emails": item.get("emails"),
                "contactEmail": item.get("contactEmail")
            })
            
        return results
        
    except Exception as e:
        add_log(f"❌ Apify API 執行失敗: {str(e)}")
        return []
