"""
製造商模式 (Manufacturer Mode) - Apify 版 2026
專為搜尋中小型 B2B 製造商設計
資料來源：Apify Thomasnet Scraper + Yellowpages 備援
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

# ══════════════════════════════════════════
# Apify 搜尋主函數
# ══════════════════════════════════════════

async def search_via_apify_thomasnet(keyword: str, market: str = "US", max_results: int = 30, db = None, user_id: int = None) -> List[Dict]:
    """使用 Apify Thomasnet Actor 搜尋製造商"""
    from config_utils import get_api_key
    apify_token = get_api_key(db, "apify", user_id)
    
    if not apify_token:
        add_log("❌ APIFY_TOKEN 未設定！請確認資料庫或環境變數", level="error")
        return []

    try:
        from apify_client import ApifyClient
        client = ApifyClient(apify_token)
    except ImportError:
        add_log("❌ 未安裝 apify-client 庫", level="error")
        return []

    try:
        add_log(f"🏭 [Apify Thomasnet] 開始搜尋：{keyword} | 市場：{market} | 目標筆數：{max_results}")

        run_input = {
            "searchTerm": keyword,           # 關鍵字（可包含 manufacturer）
            "location": "United States" if market == "US" else market,
            "maxResults": max_results,
            # 可根據 Actor 文件再加其他參數，例如 categories、minRating 等
        }

        # 優先使用 memo23 的 Actor（較穩定）
        try:
            run = client.actor("memo23/thomasnet-scraper").call(run_input=run_input)
        except Exception as e:
            add_log(f"⚠️ memo23 Actor 失敗: {str(e)[:50]}", level="warning")
            run = None

        if not run or not run.get("defaultDatasetId"):
            add_log("⚠️ 嘗試備援 Actor...", level="warning")
            # 備援 Actor
            try:
                run = client.actor("jeeves_is_my_copilot/thomasnet-supplier-directory-scraper").call(run_input=run_input)
            except Exception as e:
                add_log(f"❌ 備援 Actor 也失敗: {str(e)[:50]}", level="error")
                run = None

        if not run or not run.get("defaultDatasetId"):
            add_log("❌ 兩個 Thomasnet Actor 皆失敗", level="error")
            return []

        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items

        results = []
        for item in items:
            company_name = item.get("companyName") or item.get("name") or item.get("title", "")
            website = item.get("website") or item.get("url", "")
            domain = extract_domain(website) if website else ""

            if not company_name or len(company_name.strip()) < 3:
                continue

            # 排除大型企業
            if any(bad in company_name.lower() for bad in ENTERPRISE_BLACKLIST):
                continue

            results.append({
                "company_name": company_name.strip(),
                "website": website,
                "domain": domain,
                "snippet": item.get("description", "")[:200],
                "source": "apify_thomasnet",
            })

        add_log(f"✅ [Apify Thomasnet] 成功取得 {len(results)} 筆製造商資料")
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
    pages: int = 3,          # 這裡 pages 暫時不直接用，可改成 max_results
    user_id: int = None
) -> Dict:
    from free_email_hunter import find_emails_free, auto_discover_domain
    from models import Lead
    from config_utils import get_api_key
    
    db = SessionLocal()
    apify_token = get_api_key(db, "apify", user_id)
    
    add_log(f"🏭 [製造商模式 - Apify] 開始探勘：{keyword} | 市場：{market}")

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

    add_task_log(db, task_id, "info", f"製造商模式 (Apify) 啟動 | 關鍵字: {keyword}")

    # 直接用 Apify Thomasnet 搜尋（最有效）
    all_companies = await search_via_apify_thomasnet(keyword, market, max_results=40, db=db, user_id=user_id)

    # 如果 Thomasnet 結果太少，補充 Yellow Pages（製造商相關）
    if len(all_companies) < 15 and apify_token:
        add_task_log(db, task_id, "info", "Thomasnet 結果不足，補充 Yellow Pages 製造商...", keyword=keyword)
        try:
            from apify_client import ApifyClient
            client = ApifyClient(apify_token)
            yp_input = {
                "searchTerms": f"{keyword} manufacturer",
                "location": "United States" if market == "US" else market,
                "maxResults": 20,
            }
            run = client.actor("automation-lab/yellowpages-scraper").call(run_input=yp_input)
            if run and run.get("defaultDatasetId"):
                yp_items = client.dataset(run["defaultDatasetId"]).list_items().items
                for item in yp_items:
                    name = item.get("businessName") or item.get("name", "")
                    website = item.get("website", "")
                    domain = extract_domain(website) if website else ""
                    if name and len(name) > 3:
                        all_companies.append({
                            "company_name": name,
                            "website": website,
                            "domain": domain,
                            "snippet": "",
                            "source": "apify_yellowpages",
                        })
        except Exception as e:
            add_log(f"⚠️ Yellow Pages 備援失敗: {str(e)[:80]}", level="warning")

    if not all_companies:
        add_task_log(db, task_id, "warning", "找不到任何公司，模式中止")
        task_record.status = "Completed"
        task_record.completed_at = datetime.utcnow()
        task_record.leads_found = 0
        db.commit()
        db.close()
        return {"added": 0, "skipped": 0, "failed": 0}

    # 去重
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

    add_log(f"📊 去重後共 {len(unique_companies)} 家製造商候選")

    stats = {"added": 0, "skipped": 0, "failed": 0}
    process_limit = 25 if market == "US" else 15

    for co in unique_companies[:process_limit]:
        company_name = co["company_name"]
        domain_found = co.get("domain", "")
        
        add_task_log(db, task_id, "info", f"處理公司: {company_name}", keyword=keyword)
        
        try:
            # 檢查是否已存在
            existing = None
            if domain_found:
                existing = db.query(Lead).filter(
                    Lead.domain == domain_found,
                    Lead.user_id == user_id
                ).first()
            
            if existing:
                add_log(f"  ⏭️ 已存在：{company_name}")
                stats["skipped"] += 1
                continue

            if not domain_found:
                domain_found = await auto_discover_domain(company_name)
            
            if not domain_found:
                add_log(f"  ⚠️ 無法發現域名：{company_name}")
                stats["failed"] += 1
                continue

            # 找 email
            email_result = await find_emails_free(domain_found, company_name)
            best_email_obj = email_result.get("best_email")
            email = best_email_obj["email"] if best_email_obj else f"info@{domain_found}"

            # 儲存 Lead
            lead = Lead(
                user_id=user_id,
                company_name=company_name,
                website_url=co.get("website", ""),
                domain=domain_found,
                contact_email=email,
                ai_tag=classify_industry(co.get("snippet", "") + " " + company_name),
                status="Scraped",
                assigned_bd="Manufacturer-Mode",
                extracted_keywords=keyword,
                scrape_location=market
            )
            db.add(lead)
            db.commit()
            
            add_task_log(db, task_id, "success", f"新增 Lead: {company_name} ({email})", keyword=keyword)
            stats["added"] += 1
            
        except Exception as e:
            add_log(f"  ❌ 處理 {company_name} 錯誤: {str(e)}")
            add_task_log(db, task_id, "error", f"處理 {company_name} 失敗: {str(e)[:60]}", keyword=keyword)
            stats["failed"] += 1
        
        await asyncio.sleep(random.uniform(0.8, 1.8))  # 避免太快

    # 更新任務狀態
    task_record.status = "Completed"
    task_record.leads_found = stats["added"]
    task_record.completed_at = datetime.utcnow()
    db.commit()
    
    add_task_log(db, task_id, "success", f"製造商模式完成！新增 {stats['added']} | 跳過 {stats['skipped']} | 失敗 {stats['failed']}")
    add_log(f"🏁 [製造商模式] 完成：新增 {stats['added']} 筆")
    
    db.close()
    return stats


# 輔助函數
INDUSTRY_KEYWORDS = {
    "Auto Parts":     ["auto", "car", "vehicle", "automotive", "motor"],
    "Electronics":    ["electronic", "circuit", "PCB", "semiconductor"],
    "Plastics":       ["plastic", "injection molding", "polymer", "resin"],
    "Metal Fab":      ["metal", "steel", "aluminum", "fabrication", "casting"],
}

def classify_industry(text: str) -> str:
    text_lower = text.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return industry
    return "Manufacturing"

def extract_domain(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        if "://" not in url:
            url = f"https://{url}"
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None
    except:
        return None

if __name__ == "__main__":
    async def test():
        await manufacturer_mine("car battery", "US", 1, 1)
    asyncio.run(test())
