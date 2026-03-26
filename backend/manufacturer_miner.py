"""
製造商模式 (Manufacturer Mode v2.6) - Apify 加強版
由 Thomasnet 優先，Yellowpages 為備援
加強：Email 提取與進階去重 (Domain 優先)
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

        # 優先使用 memo23 的 Actor（較穩定）
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
                "snippet": item.get("description", "")[:200],
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
    
    add_log(f"🏭 [製造商模式 - v2.6] 開啟探勘：{keyword} | 市場：{market}")

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

    add_task_log(db, task_id, "info", f"製造商模式 (Enhanced) 啟動 | 關鍵字: {keyword}")

    # Step 1: Thomasnet
    all_companies = await search_via_apify_thomasnet(keyword, market, max_results=40, db=db, user_id=user_id)

    # Step 2: Yellowpages (Fallback with Enhanced Search)
    if len(all_companies) < 15 and apify_token:
        add_task_log(db, task_id, "info", "結果不足，啟動備援 黃頁尋機...", keyword=keyword)
        try:
            from apify_client import ApifyClient
            client = ApifyClient(apify_token)
            
            # 使用更推薦的 junipr Actor
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
                        raw_emails = item.get("email") or item.get("emails") or item.get("contactEmail") or []
                        if isinstance(raw_emails, str): raw_emails = [raw_emails]
                        elif not isinstance(raw_emails, list): raw_emails = []
                        
                        all_companies.append({
                            "company_name": name,
                            "website": website,
                            "domain": domain,
                            "email": raw_emails[0] if raw_emails else "",
                            "email_candidates": ", ".join(raw_emails),
                            "snippet": "",
                            "source": "apify_yellowpages",
                        })
        except Exception as e:
            add_log(f"⚠️ 備援尋機失敗: {str(e)[:80]}", level="warning")

    if not all_companies:
        add_task_log(db, task_id, "warning", "找不到任何公司，模式中止")
        task_record.status = "Completed"
        task_record.completed_at = datetime.utcnow()
        task_record.leads_found = 0
        db.commit()
        db.close()
        return {"added": 0, "skipped": 0, "failed": 0}

    # 去重 (Domain 優先)
    seen_domains = set()
    unique_companies = []
    for co in all_companies:
        domain = co.get("domain", "")
        if domain:
            if domain not in seen_domains:
                seen_domains.add(domain)
                unique_companies.append(co)
        else:
            if co["company_name"] not in [c["company_name"] for c in unique_companies]:
                unique_companies.append(co)

    add_log(f"📊 去重後共 {len(unique_companies)} 家候選製造商")

    stats = {"added": 0, "skipped": 0, "failed": 0}
    process_limit = 30 if market == "US" else 20

    for co in unique_companies[:process_limit]:
        company_name = co["company_name"]
        domain_found = co.get("domain", "")
        
        try:
            # ─── 進階去重邏輯 (Domain 優先 -> 名稱) ───
            existing = None
            if domain_found:
                existing = db.query(models.Lead).filter(
                    models.Lead.domain == domain_found,
                    models.Lead.user_id == user_id
                ).first()
            
            if not existing:
                existing = db.query(models.Lead).filter(
                    models.Lead.company_name == company_name,
                    models.Lead.user_id == user_id
                ).first()
            
            if existing:
                add_log(f"  ⏭️ 已存在 (去重跳過)：{company_name}")
                stats["skipped"] += 1
                continue

            # 取出 Email
            email = co.get("email", "")
            candidates = co.get("email_candidates", "")
            
            # 若 Apify 沒抓到，嘗試 Auto Discovery
            if not email and domain_found:
                email_result = await find_emails_free(domain_found, company_name)
                best_email_obj = email_result.get("best_email")
                email = best_email_obj["email"] if best_email_obj else f"info@{domain_found}"
            
            if not email:
                add_log(f"  ⚠️ 無法發現 Email：{company_name}")
                stats["failed"] += 1
                continue

            # 儲存 Lead
            lead = models.Lead(
                user_id=user_id,
                company_name=company_name,
                website_url=co.get("website", ""),
                domain=domain_found or "",
                contact_email=email,
                email_candidates=candidates,
                ai_tag="AUTO-MANUFACTURER-PRO",
                status="Scraped",
                assigned_bd="v2.6-Miner",
                extracted_keywords=keyword,
                scrape_location=market
            )
            db.add(lead)
            db.commit()
            
            add_task_log(db, task_id, "success", f"新增 Lead: {company_name} ({email})", keyword=keyword)
            stats["added"] += 1
            
        except Exception as e:
            add_log(f"❌ 處理 {company_name} 時出錯: {str(e)[:100]}", level="error")
            stats["failed"] += 1

    # 更新任務結束
    task_record.status = "Completed"
    task_record.leads_found = stats["added"]
    task_record.completed_at = datetime.utcnow()
    db.commit()
    
    summary = f"製造商模式結束 | 新增:{stats['added']} 跳過:{stats['skipped']} 失敗:{stats['failed']}"
    add_log(f"🏁 [任務 #{task_id}] {summary}")
    add_task_log(db, task_id, "success", summary)
    
    db.close()
    return stats
