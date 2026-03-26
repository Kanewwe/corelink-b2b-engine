"""
Simplified scraper - Uses Apify Yellow Pages Actor
2026 穩定版 - 取代 ScraperAPI + Mock Mode
"""

import os
import time
import models
from database import SessionLocal
from logger import add_log, add_task_log

# Apify 整合
try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False


def scrape_simple(market: str = "US", pages: int = 3, keywords: list = None, user_id: int = None):
    """
    Mine companies using multiple keywords from Yellowpages via Apify.
    Each keyword will be scraped for the specified number of pages.
    """
    if keywords is None:
        keywords = ["manufacturer"]
    
    db = SessionLocal()
    
    # Create Task Record
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
    add_log(f"   Market: {market}, Keywords: {keywords}, Pages: {pages}")
    add_task_log(db, task_id, "info", f"任務啟動 | 市場: {market} | 關鍵字: {keywords} | 頁數: {pages}")
    
    if not APIFY_AVAILABLE:
        add_task_log(db, task_id, "error", "apify-client 未安裝，降級 Mock Mode")
    
    try:
        for ki, keyword in enumerate(keywords):
            add_log(f"📌 正在爬取關鍵字 ({ki+1}/{len(keywords)}): {keyword}")
            add_task_log(db, task_id, "info", f"開始爬取關鍵字: {keyword} ({ki+1}/{len(keywords)})", keyword=keyword)
            
            for page in range(1, pages + 1):
                try:
                    add_log(f"   第 {page}/{pages} 頁開始...")
                    
                    results = scrape_keyword_page_apify(keyword, page, market, db, task_id)
                    
                    for company in results:
                        name = company.get("name", "")
                        domain = company.get("domain", "")
                        
                        if not name:
                            continue
                        
                        # Check if exists
                        existing = db.query(models.Lead).filter(
                            models.Lead.company_name == name
                        ).first()
                        
                        if existing:
                            stats["skipped"] += 1
                            continue
                        
                        # Create lead
                        lead = models.Lead(
                            user_id=user_id,
                            company_name=name,
                            website_url=company.get("url", ""),
                            domain=domain,
                            phone=company.get("phone", ""),
                            address=company.get("address", ""),
                            ai_tag="AUTO-UNKNOWN",
                            status="Scraped"
                        )
                        db.add(lead)
                        db.commit()
                        stats["saved"] += 1
                    
                    add_log(f"   第 {page}/{pages} 頁完成 (取得 {len(results)} 筆)")
                    add_task_log(
                        db, task_id, "success",
                        f"第 {page}/{pages} 頁完成 | 取得 {len(results)} 筆 | 新增 {stats['saved']} | 跳過 {stats['skipped']}",
                        keyword=keyword, page=page, items_found=len(results)
                    )
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    stats["errors"] += 1
                    err_msg = f"爬取第 {page} 頁失敗: {str(e)[:200]}"
                    add_log(f"❌ {err_msg}")
                    add_task_log(db, task_id, "error", err_msg, keyword=keyword, page=page)
        
        # Update Task Record
        task_record.status = "Completed"
        task_record.leads_found = stats["saved"]
        from datetime import datetime
        task_record.completed_at = datetime.utcnow()
        db.commit()
        
        summary = f"完成 | 新增:{stats['saved']} 跳過:{stats['skipped']} 錯誤:{stats['errors']}"
        add_log(f"🏁 [任務 #{task_id}] {summary}")
        add_task_log(db, task_id, "success", summary, items_found=stats["saved"])
        return stats
        
    except Exception as e:
        err_msg = f"任務失敗: {str(e)[:300]}"
        add_log(f"❌ [任務 #{task_id}] {err_msg}")
        add_task_log(db, task_id, "error", err_msg)
        
        try:
            task_record.status = "Failed"
            task_record.error_message = str(e)[:500]
            from datetime import datetime
            task_record.completed_at = datetime.utcnow()
            db.commit()
        except:
            pass
        raise
    finally:
        db.close()


def scrape_keyword_page_apify(keyword: str, page: int, market: str = "US", db=None, task_id: int = None) -> list:
    """
    使用 Apify 官方 Yellow Pages Actor 爬取真實資料
    Actor ID: automation-lab/yellowpages-scraper
    """
    api_token = os.getenv("APIFY_API_TOKEN")
    
    if not api_token or not APIFY_AVAILABLE:
        add_log("⚠️ Apify 未設定，啟動 Mock Mode")
        if db and task_id:
            add_task_log(db, task_id, "warning", "Apify 未設定或不可用，降級 Mock Mode", keyword=keyword, page=page)
        return get_mock_results(keyword, page)
    
    client = ApifyClient(api_token)
    
    # 地點對照
    location_map = {
        "US": "United States",
        "USA": "United States",
        "EU": "Europe",
        "TW": "Taiwan",
        "CA": "Canada",
        "UK": "United Kingdom",
        "AU": "Australia"
    }
    location = location_map.get(market, market)
    
    # Apify Actor 輸入參數
    run_input = {
        "searchTerms": keyword,
        "location": location,
        "maxResults": 30 * page,
    }
    
    try:
        add_log(f"🌐 [Apify] 開始爬取 → 關鍵字: {keyword} | 地點: {location} | 目標: {run_input['maxResults']} 筆")
        
        # 執行 Actor
        run = client.actor("automation-lab/yellowpages-scraper").call(run_input=run_input)
        
        if not run:
            add_log("⚠️ Apify Actor 執行失敗，降級 Mock Mode")
            if db and task_id:
                add_task_log(db, task_id, "warning", "Apify Actor 執行回傳 None，降級 Mock Mode", keyword=keyword, page=page)
            return get_mock_results(keyword, page)
        
        # 取回結果
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        results = []
        for item in items:
            website = item.get("website", "")
            domain = ""
            if website and website.startswith("http"):
                from urllib.parse import urlparse
                domain = urlparse(website).netloc.replace("www.", "")
            
            # 組合地址
            address_parts = [
                item.get('address', ''),
                item.get('city', ''),
                item.get('state', ''),
                item.get('zipCode', '')
            ]
            address = " ".join(filter(None, address_parts)).strip()
            
            results.append({
                "name": item.get("businessName") or item.get("name", ""),
                "domain": domain,
                "url": website,
                "phone": item.get("phone", ""),
                "address": address
            })
        
        add_log(f"✅ [Apify] 成功取得 {len(results)} 筆真實資料")
        return results
        
    except Exception as e:
        err_msg = f"Apify 錯誤: {str(e)[:200]}，降級 Mock Mode"
        add_log(f"❌ {err_msg}")
        if db and task_id:
            add_task_log(db, task_id, "error", err_msg, keyword=keyword, page=page)
        return get_mock_results(keyword, page)


def get_mock_results(keyword: str, page: int) -> list:
    """
    Mock Mode - 當 Apify 失敗時的降級方案
    """
    add_log(f"💡 [Mock Mode] 生成測試資料...")
    results = []
    for i in range(1, 11):
        results.append({
            "name": f"Mock {keyword.title()} Corp {page}-{i}",
            "domain": f"mock-{keyword.replace(' ', '')}{page}{i}.com",
            "url": f"https://www.mock-{keyword.replace(' ', '')}{page}{i}.com",
            "phone": f"+1-555-010{page}{i}",
            "address": f"{1000 + i} Test Ave, Tech City, CA"
        })
    return results


if __name__ == "__main__":
    scrape_simple("US", 1, ["cable manufacturer"])
