"""
製造商模式 (Manufacturer Mode v2.7) - Apify 加強版
由 Thomasnet 優先，Yellowpages 為備援
加強：Email 提取、進階去重 (Domain 優先) 與 全域隔離池 (Global Lead Pool) 同步
"""

import asyncio
import random
import os
from urllib.parse import urlparse
from typing import List, Dict, Optional
from logger import add_log, add_task_log
import models
from database import SessionLocal
from datetime import datetime
from scrape_utils import sync_from_global_pool, save_to_global_pool, extract_best_email
import ai_service
from config_utils import get_general_setting

# ── 公司規模過濾詞（排除大型跨國企業）──
ENTERPRISE_BLACKLIST = [
    "bosch", "siemens", "honeywell", "3m", "johnson", "ge ", "ford",
    "toyota", "samsung", "lg ", "apple", "amazon", "walmart",
]


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


# ══════════════════════════════════════════
# Apify 搜尋主函數
# ══════════════════════════════════════════

async def search_via_apify_thomasnet(keyword: str, market: str = "US", max_results: int = 30, db = None, user_id: int = None) -> List[Dict]:
    """使用 Apify Thomasnet Actor 搜尋製造商"""
    from config_utils import get_api_key
    apify_token = get_api_key(db, "apify", user_id)
    
    if not apify_token:
        add_log("❌ APIFY_TOKEN 未設定！", level="error")
        return []

    try:
        from apify_client import ApifyClient
        client = ApifyClient(apify_token)
    except ImportError:
        add_log("❌ 未安裝 apify-client 庫", level="error")
        return []

    try:
        add_log(f"🏭 [Apify Thomasnet] 開始搜尋：{keyword} | 地點：{market}")

        run_input = {
            "searchTerm": keyword,
            "location": "United States" if market == "US" else market,
            "maxResults": max_results,
            "extractEmails": True, # 加強 Email 提取
            "includeDetails": True # 深層資訊提取
        }

        # 優先使用 memo23 的 Actor
        try:
            run = client.actor("memo23/thomasnet-scraper").call(run_input=run_input)
        except Exception:
            run = None

        if not run or not run.get("defaultDatasetId"):
            add_log("⚠️ 嘗試備援 Thomasnet Actor...", level="warning")
            try:
                run = client.actor("jeeves_is_my_copilot/thomasnet-supplier-directory-scraper").call(run_input=run_input)
            except Exception:
                run = None

        if not run or not run.get("defaultDatasetId"):
            add_log("❌ Thomasnet Actor 皆失敗", level="error")
            return []

        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items

        results = []
        for item in items:
            company_name = (item.get("companyName") or item.get("name") or item.get("title", "")).strip()
            website = (item.get("website") or item.get("url", "")).strip()
            domain = extract_domain(website)

            if not company_name or len(company_name) < 3:
                continue

            # 排除大型企業
            if any(bad in company_name.lower() for bad in ENTERPRISE_BLACKLIST):
                continue
            
            # Email 處理
            raw_emails = item.get("email") or item.get("emails") or item.get("contactEmail") or []
            if isinstance(raw_emails, str): raw_emails = [raw_emails]
            elif not isinstance(raw_emails, list): raw_emails = []
            
            results.append({
                "company_name": company_name,
                "website": website,
                "domain": domain,
                "description": item.get("description", "")[:500],
                "email": raw_emails[0] if raw_emails else "",
                "email_candidates": ", ".join(raw_emails),
                "source": "apify_thomasnet",
            })

        add_log(f"✅ [Apify Thomasnet] 成功取得 {len(results)} 筆資料")
        return results

    except Exception as e:
        add_log(f"❌ Apify Thomasnet 執行錯誤: {str(e)[:120]}", level="error")
        return []


# ══════════════════════════════════════════
# 主入口函數
# ══════════════════════════════════════════

async def manufacturer_mine(
    keyword: str,
    market: str = "US",
    pages: int = 3,
    user_id: int = None
) -> Dict:
    from free_email_hunter import find_emails_free, auto_discover_domain
    from models import Lead
    from config_utils import get_api_key
    
    db = SessionLocal()
    apify_token = get_api_key(db, "apify", user_id)
    
    add_log(f"🏭 [製造商模式 - v2.7] 開啟探勘：{keyword}")

    task_record = models.ScrapeTask(
        user_id=user_id,
        market=market,
        keywords=keyword,
        miner_mode="manufacturer",
        pages_requested=pages,
        status="Running"
    )
    db.add(task_record)
    db.commit()
    db.refresh(task_record)
    task_id = task_record.id

    add_task_log(db, task_id, "info", f"製造商模式 (GlobalPool Sync) 啟動 | 關鍵字: {keyword}")

    # Step 1: Thomasnet
    all_companies = await search_via_apify_thomasnet(keyword, market, max_results=40, db=db, user_id=user_id)

    # Step 2: Yellowpages (Fallback)
    if len(all_companies) < 15 and apify_token:
        add_task_log(db, task_id, "info", "結果不足，啟動備援 黃頁尋機...", keyword=keyword)
        try:
            from apify_client import ApifyClient
            client = ApifyClient(apify_token)
            yp_input = {
                "searchTerms": [f"{keyword} manufacturer"],
                "location": "United States" if market == "US" else market,
                "maxResults": 20,
                "extractEmails": True,
                "includeDetails": True
            }
            run = client.actor("junipr/yellow-pages-scraper").call(run_input=yp_input)
            if run and run.get("defaultDatasetId"):
                yp_items = client.dataset(run["defaultDatasetId"]).list_items().items
                for item in yp_items:
                    name = (item.get("businessName") or item.get("name", "")).strip()
                    website = (item.get("website") or item.get("url", "")).strip()
                    domain = extract_domain(website)
                    
                    if name and len(name) > 3:
                        # 提取最佳 Email
                        email = extract_best_email(item)
                        
                        email_candidates_str = ""
                        raw_emails = item.get("email") or item.get("emails") or item.get("contactEmail") or []
                        if isinstance(raw_emails, list):
                            email_candidates_str = ", ".join([str(e) for e in raw_emails if e])
                        elif isinstance(raw_emails, str):
                            email_candidates_str = raw_emails
                        
                        all_companies.append({
                            "company_name": name,
                            "website": website,
                            "domain": domain,
                            "description": item.get("description", ""),
                            "email": raw_emails[0] if raw_emails else "",
                            "email_candidates": ", ".join(raw_emails),
                            "source": "apify_yellowpages",
                        })
        except Exception as e:
            add_log(f"⚠️ 備援尋機失敗: {str(e)[:80]}", level="warning")

    if not all_companies:
        task_record.status = "Completed"
        task_record.completed_at = datetime.utcnow()
        db.commit()
        db.close()
        return {"added": 0, "synced": 0, "skipped": 0}

    stats = {"added": 0, "synced": 0, "skipped": 0, "failed": 0}
    process_limit = 40
    from config_utils import get_general_setting
    sync_enabled = get_general_setting(db, "enable_global_sync", default=True, user_id=user_id)

    for co in all_companies[:process_limit]:
        company_name = co["company_name"]
        domain_found = co.get("domain", "")
        
        try:
            # ─── v2.7.1: 全域隔離池同步邏輯 (考慮 sync_enabled) ───
            lead_obj, is_synced = sync_from_global_pool(db, user_id, domain_found, company_name, sync_enabled=sync_enabled)
            
            if lead_obj and not is_synced:
                stats["skipped"] += 1
                continue
            
            if is_synced:
                stats["synced"] += 1
                continue

            # ─── 全新名單處理 ───
            desc = co.get("description", "") or f"Manufacturer found via {co.get('source')}"
            ai_result = ai_service.analyze_company_and_tag(company_name, desc, use_gpt=False, db=db, user_id=user_id)
            
            email = co.get("email", "")
            candidates = co.get("email_candidates", "")
            
            if not email and domain_found:
                email_result = await find_emails_free(domain_found, company_name)
                best_email_obj = email_result.get("best_email")
                email = best_email_obj["email"] if best_email_obj else f"info@{domain_found}"
            
            if not email:
                stats["failed"] += 1
                continue

            # 儲存私有 Lead
            new_lead = models.Lead(
                user_id=user_id,
                company_name=company_name,
                website_url=co.get("website", ""),
                domain=domain_found or "",
                description=desc,
                contact_email=email,
                email_candidates=candidates,
                ai_tag=ai_result.get("Tag", "AUTO-MANUFACTURER-PRO"),
                industry_taxonomy=ai_result.get("Taxonomy"), # v3.0
                status="Scraped",
                assigned_bd=ai_result.get("BD", "v2.7-Miner"),
                extracted_keywords=keyword,
                scrape_location=market
            )
            db.add(new_lead)
            db.commit()
            db.refresh(new_lead)
            
            # 同步回全域池 (Shared Intelligence Layer - v3.0)
            global_rec = save_to_global_pool(db, {
                "company_name": company_name,
                "domain": domain_found,
                "website_url": co.get("website"),
                "description": desc,
                "contact_email": email,
                "email_candidates": candidates,
                "ai_tag": ai_result.get("Tag"),
                "industry_taxonomy": ai_result.get("Taxonomy"),
                "source": co.get("source")
            })
            
            if global_rec:
                new_lead.global_id = global_rec.id
                db.commit()
            
            # 連結 global_id
            global_rec = db.query(models.GlobalLead).filter(models.GlobalLead.domain == domain_found).first()
            if global_rec:
                new_lead.global_id = global_rec.id
                db.commit()

            add_task_log(db, task_id, "success", f"新增 Lead: {company_name}", keyword=keyword)
            stats["added"] += 1
            
        except Exception as e:
            add_log(f"❌ 處理 {company_name} 時出錯: {str(e)[:100]}", level="error")
            stats["failed"] += 1

    # 更新任務結束
    task_record.status = "Completed"
    task_record.leads_found = stats["added"] + stats["synced"]
    task_record.completed_at = datetime.utcnow()
    db.commit()
    
    summary = f"製造商模式結束 | 新增:{stats['added']} 同步:{stats['synced']} 跳過:{stats['skipped']}"
    add_log(f"🏁 [任務 #{task_id}] {summary}")
    add_task_log(db, task_id, "success", summary)
    
    db.close()
    return stats
