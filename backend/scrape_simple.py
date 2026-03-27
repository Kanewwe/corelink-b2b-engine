"""
Simplified scraper - Uses Apify Yellow Pages Actor (Enhanced v3.2)
2026 穩定版 - 整合 Email 撈取、進階去重與 全域隔離池 (Global Lead Pool) 同步

v3.2 修復:
- 用量檢查：爬蟲開始前檢查配額
- 用量計算：新增 Lead 後調用 increment_usage
- Email 補強：完整三層 email 發現策略（Apify → find_emails_free → Guessing）
"""

import os
import time
import models
from database import SessionLocal
from logger import add_log, add_task_log
from urllib.parse import urlparse
from datetime import datetime
from scrape_utils import sync_from_global_pool, save_to_global_pool, extract_best_email
from config_utils import get_general_setting
import ai_service
import auth as auth_module

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


def scrape_simple(market: str = "US", pages: int = 3, keywords: list = None, user_id: int = None, email_strategy: str = "free"):
    """
    使用黃頁模式 (Apify) 探勘公司。
    v3.2: email_strategy 參數 ("free" 或 "hunter")
    """
    if keywords is None:
        keywords = ["manufacturer"]
    
    db = SessionLocal()
    sync_enabled = get_general_setting(db, "enable_global_sync", default=True, user_id=user_id)
    
    # ═══ v2.7.3: 用量檢查 ═══
    usage_check = auth_module.check_user_quota(db, user_id, "customers")
    if not usage_check["allowed"]:
        add_log(f"⚠️ [配額檢查] 用戶 {user_id} 配額已滿: {usage_check['message']}")
        task_record = models.ScrapeTask(
            user_id=user_id,
            market=market,
            keywords=",".join(keywords),
            miner_mode="yellowpages",
            pages_requested=pages,
            status="Failed",
            error_message=usage_check["message"]
        )
        db.add(task_record)
        db.commit()
        db.close()
        return {"saved": 0, "synced": 0, "skipped": 0, "errors": 0, "quota_exceeded": True}
    
    remaining_quota = usage_check.get("remaining", -1)
    add_log(f"✅ [配額檢查] 用戶 {user_id} 剩餘配額: {remaining_quota}")
    
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
    new_leads_count = 0  # v2.7.3: 追蹤新增數量
    
    add_log(f"🔍 [Apify 爬蟲] 開始任務 #{task_id}")
    add_task_log(db, task_id, "info", f"任務啟動 | 市場: {market} | 關鍵字: {keywords} | 配額: {remaining_quota}")
    
    if not APIFY_AVAILABLE:
        add_task_log(db, task_id, "error", "apify-client 未安裝")
        db.close()
        return stats
    
    try:
        for ki, keyword in enumerate(keywords):
            # v2.7.3: 檢查是否還有配額
            if remaining_quota != -1 and new_leads_count >= remaining_quota:
                add_task_log(db, task_id, "warning", f"配額已用完，停止爬取 | 已新增: {new_leads_count}")
                break
                
            add_log(f"📌 正在爬取關鍵字 ({ki+1}/{len(keywords)}): {keyword}")
            add_task_log(db, task_id, "info", f"開始處理關鍵字: {keyword}", keyword=keyword)
            
            for page in range(1, pages + 1):
                # v2.7.3: 每頁開始前也檢查配額
                if remaining_quota != -1 and new_leads_count >= remaining_quota:
                    break
                    
                try:
                    results = scrape_keyword_page_apify(keyword, page, market, db, task_id, user_id)
                    
                                # ─── v3.2.1: Email 補強並行處理 ───
                    from concurrent.futures import ThreadPoolExecutor, as_completed

                    def _enrich_one(item):
                        """在緒程中處理一個 item，含 email 補強與入庫"""
                        local_db = SessionLocal()
                        try:
                            name = item.get("name", "").strip()
                            website = item.get("url", "").strip()
                            domain = extract_domain(website)
                            if not name: return None

                            # 去重檢查
                            lead_obj, is_synced = sync_from_global_pool(local_db, user_id, domain, name, sync_enabled=sync_enabled)
                            if lead_obj: return None  # 既存或已同步
                            if remaining_quota != -1 and new_leads_count >= remaining_quota: return None

                            # AI 標籤
                            desc = item.get("description", "") or "Business listing"
                            ai_result = ai_service.analyze_company_and_tag(name, desc, use_gpt=False, db=local_db, user_id=user_id)

                            # Email 三層
                            contact_email = extract_best_email(item)
                            candidate_list = []
                            email_source = "apify"
                            for src_field in ["email", "emails", "contactEmail"]:
                                val = item.get(src_field)
                                if val and isinstance(val, str) and "@" in val:
                                    contact_email = val; candidate_list.append(val); break

                            if not contact_email and domain:
                                try:
                                    if email_strategy == "hunter":
                                        from email_hunter import find_target_contacts
                                        from config_utils import get_api_key
                                        hkey = get_api_key(local_db, "hunter", user_id)
                                        if hkey:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            try:
                                                hr = loop.run_until_complete(find_target_contacts(name, website, hkey))
                                                if hr.get("primary_contact"):
                                                    contact_email = hr["primary_contact"].get("email", "")
                                                    candidate_list.extend(hr.get("emails", [])); email_source = "hunter"
                                            finally: loop.close()
                                    else:
                                        from free_email_hunter import find_emails_free
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            er = loop.run_until_complete(find_emails_free(domain, name, timeout=5))
                                            best = er.get("best_email")
                                            if best and best.get("email"):
                                                contact_email = best["email"]
                                                candidate_list.extend(er.get("candidates", [])); email_source = "website"
                                        finally: loop.close()
                                except: pass

                            if not contact_email and domain:
                                for prefix in ["info", "sales", "contact"]:
                                    guess = f"{prefix}@{domain}"
                                    if len(guess) > 5:
                                        candidate_list.append(guess); email_source = "guessed"; break

                            candidates_str = ", ".join(candidate_list)

                            # 入庫
                            new_lead = models.Lead(
                                user_id=user_id, company_name=name, website_url=website, domain=domain,
                                description=desc, phone=item.get("phone",""), address=item.get("address",""),
                                city=item.get("city",""), state=item.get("state",""), zip_code=item.get("zipCode",""),
                                contact_email=contact_email, email_candidates=candidates_str,
                                ai_tag=ai_result.get("Tag","AUTO-YELLOWPAGES"),
                                industry_taxonomy=ai_result.get("Taxonomy"),
                                status="Scraped", scrape_location=market, extracted_keywords=keyword,
                                assigned_bd=ai_result.get("BD","General")
                            )
                            local_db.add(new_lead); local_db.commit(); local_db.refresh(new_lead)

                            # 全域池
                            g_email = contact_email if email_source in ("apify","website","hunter") else None
                            global_rec = save_to_global_pool(local_db, {
                                "company_name": name, "domain": domain, "website_url": website,
                                "description": desc, "contact_email": g_email, "email_candidates": candidates_str,
                                "phone": item.get("phone",""), "ai_tag": ai_result.get("Tag"),
                                "industry_taxonomy": ai_result.get("Taxonomy"), "source": "apify_yellowpages"
                            })
                            if global_rec:
                                new_lead.global_id = global_rec.id; local_db.commit()

                            auth_module.increment_usage(local_db, user_id, "customers_count", 1)
                            return 1
                        except Exception as e:
                            add_log(f"❌ _enrich_one: {str(e)[:60]}")
                            return None
                        finally:
                            local_db.close()

                    # v3.2.1: 緒程池並行（max 5 緒程）
                    enriched = skipped = 0
                    with ThreadPoolExecutor(max_workers=5) as pool:
                        futures = {pool.submit(_enrich_one, item): item for item in results}
                        for f in as_completed(futures):
                            try:
                                r = f.result(timeout=15)
                                if r == 1: enriched += 1; new_leads_count += 1
                                else: skipped += 1
                            except: skipped += 1

                    stats["saved"] += enriched; stats["skipped"] += skipped
                    add_task_log(db, task_id, "info", f"✅ 入庫完成: 新增 {enriched}, 跳過 {skipped}", keyword=keyword)


                        # 3. 儲存私有 Lead
                        lead_domain = item.get("domain") or extract_domain(item.get("url"))
                        lead_name = item.get("name")
                        lead_website = item.get("url")
                        
                        new_lead = models.Lead(
                            user_id=user_id,
                            company_name=lead_name,
                            website_url=lead_website,
                            domain=lead_domain,
                            description=description,
                            phone=item.get("phone", ""),
                            address=item.get("address", ""),
                            city=item.get("city", ""),
                            state=item.get("state", ""),
                            zip_code=item.get("zipCode", ""),
                            contact_email=contact_email,
                            email_candidates=email_candidates_str,
                            ai_tag=ai_result.get("Tag", "AUTO-YELLOWPAGES"),
                            industry_taxonomy=ai_result.get("Taxonomy"),
                            status="Scraped",
                            scrape_location=market,
                            extracted_keywords=keyword,
                            assigned_bd=ai_result.get("BD", "General")
                        )
                        db.add(new_lead)
                        db.commit()
                        db.refresh(new_lead)
                        stats["saved"] += 1
                        new_leads_count += 1  # v2.7.3: 追蹤新增數量
                        
                        # v2.7.3: 增加用量計數
                        auth_module.increment_usage(db, user_id, "customers_count", 1)
                        
                        # 4. 同步回全域池 (Shared Intelligence Layer - v3.0)
                        global_rec = save_to_global_pool(db, {
                            "company_name": lead_name,
                            "domain": lead_domain,
                            "website_url": lead_website,
                            "description": description,
                            "contact_email": contact_email,
                            "email_candidates": email_candidates_str,
                            "phone": item.get("phone", ""),
                            "address": item.get("address", ""),
                            "ai_tag": ai_result.get("Tag"),
                            "industry_taxonomy": ai_result.get("Taxonomy"),
                            "source": "apify_yellowpages"
                        })
                        
                        # 連結 global_id
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
    # v3.2: searchTerms 應為字串（非陣列），否則返回垃圾資料
    run_input = {
        "searchTerms": keyword,
        "location": location,
        "maxResults": 20,
        "extractEmails": True,
        "includeDetails": True
    }
    
    def _log(level, msg):
        if db and task_id:
            add_task_log(db, task_id, level, msg, keyword=keyword)
    
    try:
        _log("info", f"🌐 呼叫 Apify: {actor_id} | 關鍵字: {keyword}")
        run = client.actor(actor_id).call(run_input=run_input)
        
        if not run or not run.get("defaultDatasetId"):
            _log("warning", "主 Actor 無 dataset，切換備援 Actor")
            run = client.actor("automation-lab/yellowpages-scraper").call(run_input={
                "searchTerms": keyword, "location": location, "maxResults": 20
            })

        if not run or not run.get("defaultDatasetId"): 
            _log("error", "所有 Actor 都無法取得 dataset")
            return []
            
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        _log("info", f"📦 Apify 回傳 {len(items)} 筆原始資料")
        
        results = []
        for item in items:
            name = item.get("businessName") or item.get("name") or ""
            website = item.get("website") or item.get("url") or ""
            # v3.2: 過濾明顯的垃圾資料（餐廳常見名）
            bad_patterns = ["restaurant", "pizza", "cafe", "coffee", "bar ", "grill", "diner", "bakery", "deli"]
            if name and any(bp in name.lower() for bp in bad_patterns):
                _log("warning", f"⚠️ 過濾非目標公司: {name}")
                continue
            
            results.append({
                "name": name,
                "url": website,
                "phone": item.get("phone", ""),
                "description": item.get("description", ""),
                "address": item.get("address", "") or item.get("street", ""),
                "email": item.get("email"),
                "emails": item.get("emails"),
                "contactEmail": item.get("contactEmail"),
                "city": item.get("city", ""),
                "state": item.get("state", ""),
                "zipCode": item.get("zipCode", "")
            })
        
        _log("info", f"✅ 過濾後有效資料: {len(results)} 筆")
        return results
    except Exception as e:
        _log("error", f"❌ Apify API 失敗: {str(e)[:100]}")
        return []

if __name__ == "__main__":
    scrape_simple("US", 1, ["metal factory"])
