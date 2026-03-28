"""
製造商模式 (Manufacturer Mode v2.7.3) - Apify 加強版
由 Thomasnet 優先，Yellowpages 為備援
加強：Email 提取、進階去重 (Domain 優先) 與 全域隔離池 (Global Lead Pool) 同步

v2.7.3 修復:
- 用量檢查：爬蟲開始前檢查配額
- 用量計算：新增 Lead 後調用 increment_usage
- 全域池同步計入配額（業務決策：同步也算使用量）
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
import auth as auth_module

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
        if db and task_id:
            add_task_log(db, task_id, "info", "🏭 [Apify] 已連線至 Apify API，準備啟動 Thomasnet Actor...")
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

        # 🚀 升級 Actor: 使用 zen-studio/thomasnet-suppliers-scraper (Rising Star 2026)
        actor_id = get_api_key(db, "apify_miner_actor", user_id) or "zen-studio/thomasnet-suppliers-scraper"
        
        try:
            if db and task_id:
                add_task_log(db, task_id, "info", f"🚀 [Apify] 正在執行 Thomasnet 深度探勘 ({actor_id})...")
            
            # 🛡️ 加上 180 秒強制超時，防卡死
            run = await asyncio.wait_for(
                asyncio.to_thread(client.actor(actor_id).call, run_input=run_input),
                timeout=180
            )
        except asyncio.TimeoutError:
            add_log(f"🚨 [Apify] Thomasnet Actor ({actor_id}) 超時被終止", level="error")
            run = None
        except Exception as e:
            add_log(f"⚠️ Thomasnet Actor 執行失敗: {str(e)[:100]}，嘗試進入備援方案...", level="warning")
            run = None

        if not run or not run.get("defaultDatasetId"):
            # 備援 Actor (Dynamic Backup possible via system_settings too, but here we hardcode stable secondary)
            backup_actor = "jeeves_is_my_copilot/thomasnet-supplier-directory-scraper"
            add_log(f"⚠️ [RESILIENCE] 嘗試備援 Thomasnet Actor: {backup_actor}...", level="warning")
            try:
                run = await asyncio.wait_for(
                    asyncio.to_thread(client.actor(backup_actor).call, run_input=run_input),
                    timeout=120
                )
            except Exception:
                run = None

        if not run or not run.get("defaultDatasetId"):
            add_log("❌ Thomasnet Actor 皆失敗", level="error")
            return []

        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        # 🆕 [RESILIENCE] 檢查是否成功但 0 筆
        if not items:
            add_log(f"⚠️ [RESILIENCE] Actor {actor_id} 成功但返回 0 筆資料 (Items=0)。建議檢查 Actor 是否下架或頁面結構變更。", level="warning")
            return []

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
        if db and task_id:
            add_task_log(db, task_id, "success", f"✅ [Apify] Thomasnet 探勘完成，取得 {len(results)} 筆原始資料")
        return results

    except Exception as e:
        add_log(f"❌ Apify Thomasnet 執行錯誤: {str(e)[:120]}", level="error")
        # Ensure we return what we found so far rather than an empty list
        return results if results else []


# ══════════════════════════════════════════
# 主入口函數
# ══════════════════════════════════════════

async def manufacturer_mine(
    keyword: str,
    market: str = "US",
    pages: int = 3,
    user_id: int = None,
    email_strategy: str = "free"
) -> Dict:
    from free_email_hunter import find_emails_free, auto_discover_domain
    from models import Lead
    from config_utils import get_api_key
    
    db = SessionLocal()
    apify_token = get_api_key(db, "apify", user_id)
    
    add_log(f"🏭 [製造商模式 - v2.7.3] 開啟探勘：{keyword}")
    
    # ═══ v2.7.3: 用量檢查 ═══
    usage_check = auth_module.check_user_quota(db, user_id, "customers")
    if not usage_check["allowed"]:
        add_log(f"⚠️ [配額檢查] 用戶 {user_id} 配額已滿: {usage_check['message']}")
        task_record = models.ScrapeTask(
            user_id=user_id,
            market=market,
            keywords=keyword,
            miner_mode="manufacturer",
            pages_requested=pages,
            status="Failed",
            error_message=usage_check["message"]
        )
        db.add(task_record)
        db.commit()
        db.close()
        return {"added": 0, "synced": 0, "skipped": 0, "failed": 0, "quota_exceeded": True}
    
    remaining_quota = usage_check.get("remaining", -1)
    add_log(f"✅ [配額檢查] 用戶 {user_id} 剩餘配額: {remaining_quota}")

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

    add_task_log(db, task_id, "info", f"製造商模式啟動 | 關鍵字: {keyword} | 配額: {remaining_quota}")

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
            run = await asyncio.to_thread(client.actor("junipr/yellow-pages-scraper").call, run_input=yp_input)
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
        task_record.leads_found = 0
        db.commit()
        db.close()
        add_log(f"⚠️ [任務 #{task_id}] 未找到任何製造商資料")
        return {"added": 0, "synced": 0, "skipped": 0}

    stats = {"added": 0, "synced": 0, "skipped": 0, "failed": 0}
    new_leads_count = 0  # v2.7.3: 追蹤新增數量
    process_limit = 40
    from config_utils import get_general_setting
    sync_enabled = get_general_setting(db, "enable_global_sync", default=True, user_id=user_id)

    try:
        for co in all_companies[:process_limit]:
            # v2.7.3: 即時檢查配額
            if remaining_quota != -1 and new_leads_count >= remaining_quota:
                add_task_log(db, task_id, "warning", f"配額已用完，停止處理 | 已新增: {new_leads_count}")
                break
            
            company_name = co["company_name"]
            domain_found = co.get("domain", "")
            
            try:
                # ─── v2.7.1: 全域隔離池同步邏輯 ───
                lead_obj, is_synced = sync_from_global_pool(db, user_id, domain_found, company_name, sync_enabled=sync_enabled)
                
                if is_synced:
                    stats["synced"] += 1
                    new_leads_count += 1  # v2.7.3: 同步也計入配額
                    auth_module.increment_usage(db, user_id, "customers_count", 1)
                    continue
                    
                if lead_obj:
                    # 代表私有工作區已有 (既存重複)
                    stats["skipped"] += 1
                    continue

                # ─── 行業與標籤處理 (v3.0) ───
                desc = co.get("description", "") or f"Manufacturer found via {co.get('source')}"
                ai_result = ai_service.analyze_company_and_tag(company_name, desc, use_gpt=False, db=db, user_id=user_id)
                
                # v3.2: Email 三層補強策略
                contact_email = ""      # 已驗證 email → 寫入 contact_email
                email_candidates_list = []  # 所有找到的 email（包括候選）
                email_source_type = "none"
                
                # Layer 1: 從爬蟲來源直接取得
                for src_field in ["email", "emails", "contactEmail"]:
                    val = co.get(src_field)
                    if val:
                        if isinstance(val, str) and "@" in val:
                            contact_email = val
                            email_candidates_list.append(val)
                            email_source_type = "scraper"
                            break
                        elif isinstance(val, list):
                            for e in val:
                                if isinstance(e, str) and "@" in e:
                                    contact_email = e
                                    email_candidates_list.append(e)
                                    email_source_type = "scraper"
                                    break
                
                # Layer 2: 若無 email，嘗試加強
                if not contact_email and domain_found:
                    try:
                        if email_strategy == "hunter":
                            # Hunter.io 付費模式
                            from email_hunter import find_target_contacts
                            from config_utils import get_api_key
                            hunter_key = get_api_key(db, "hunter", user_id)
                            if hunter_key:
                                hunter_result = await find_target_contacts(company_name, co.get("website"), hunter_key)
                                if hunter_result.get("primary_contact"):
                                    contact_email = hunter_result["primary_contact"]["email"]
                                    email_candidates_list.extend(hunter_result.get("emails", []))
                                    email_source_type = "hunter"
                                    add_task_log(db, task_id, "info", f"📧 Hunter.io: {contact_email}", keyword=keyword)
                            else:
                                add_task_log(db, task_id, "warning", "⚠️ Hunter Key 未設定，降級為 free", keyword=keyword)
                        
                        if not contact_email:
                            # free 模式：從官網爬取
                            email_result = await find_emails_free(domain_found, company_name, user_id=user_id)
                            best = email_result.get("best_email")
                            if best and best.get("email"):
                                contact_email = best["email"]
                                email_candidates_list.extend(email_result.get("candidates", []))
                                email_source_type = "website"
                                add_task_log(db, task_id, "info", f"📧 官網爬取: {contact_email}", keyword=keyword)
                    except Exception as e:
                        add_task_log(db, task_id, "warning", f"⚠️ Email 補強失敗: {str(e)[:60]}", keyword=keyword)
                
                # Layer 3: Domain Prefix Guessing（最終備援）
                if not contact_email and domain_found:
                    for prefix in ["info", "sales", "contact", "hello", "admin"]:
                        guess = f"{prefix}@{domain_found}"
                        if len(guess) > 5:
                            email_candidates_list.append(guess)
                            email_source_type = "guessed"
                            add_task_log(db, task_id, "info", f"💡 Guessing: {guess}", keyword=keyword)
                            break  # 只加一個，避免過多垃圾
                
                if not contact_email and not email_candidates_list:
                    stats["failed"] += 1
                    continue
                
                # 組合 email_candidates 字串
                candidates_str = ", ".join(email_candidates_list) if email_candidates_list else ""

                # 儲存私有 Lead（contact_email 可能為空字串，此時 email_candidates 有值）
                new_lead = models.Lead(
                    user_id=user_id,
                    company_name=company_name,
                    website_url=co.get("website", ""),
                    domain=domain_found or "",
                    description=desc,
                    contact_email=contact_email,  # 可能為空，但至少 candidates 有值
                    email_candidates=candidates_str,
                    ai_tag=ai_result.get("Tag", "AUTO-MAN"),
                    industry_taxonomy=ai_result.get("Taxonomy"),
                    status="Scraped",
                    assigned_bd=ai_result.get("BD", "v3.1-Miner"),
                    extracted_keywords=keyword,
                    scrape_location=market
                )
                db.add(new_lead)
                db.commit()
                db.refresh(new_lead)
                
                # v3.2: 只有已驗證的 email 才寫入全域池
                global_email_data = contact_email if email_source_type in ("scraper", "website", "hunter") else None
                global_candidates = candidates_str  # 所有 candidates 都同步到全域
                
                global_rec = save_to_global_pool(db, {
                    "company_name": company_name,
                    "domain": domain_found,
                    "website_url": co.get("website"),
                    "description": desc,
                    "contact_email": global_email_data,  # 只有驗證過的才寫入全域 contact_email
                    "email_candidates": global_candidates,  # 猜測的存到 candidates
                    "ai_tag": ai_result.get("Tag"),
                    "industry_taxonomy": ai_result.get("Taxonomy"),
                    "source": co.get("source")
                })
                
                if global_rec:
                    new_lead.global_id = global_rec.id
                    db.commit()

                stats["added"] += 1
                new_leads_count += 1  # v2.7.3: 追蹤新增數量
                
                # v2.7.3: 增加用量計數
                auth_module.increment_usage(db, user_id, "customers_count", 1)
                
                # 💓 心跳日誌：每 5 筆回報一次
                if stats["added"] % 5 == 0:
                    add_task_log(db, task_id, "info", f"探勘進度: 已新增 {stats['added']} 筆, 同步 {stats['synced']} 筆...", keyword=keyword)
                
            except Exception as e:
                db.rollback() 
                add_log(f"❌ 處理 {company_name} 時出錯: {str(e)[:100]}", level="error")
                stats["failed"] += 1
                
        # --- 正常結束邏輯 (與 for 迴圈對齊) ---
        task_record.status = "Completed"
        task_record.leads_found = stats["added"] + stats["synced"]
        task_record.completed_at = datetime.utcnow()
        db.commit()
        
        summary = f"製造商模式結束 | 新增:{stats['added']} 同步:{stats['synced']} 跳過:{stats['skipped']}"
        add_log(f"🏁 [任務 #{task_id}] {summary}")
        add_task_log(db, task_id, "success", summary)
        
        return stats
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        add_log(f"🚨 [ManufacturerMiner] 嚴重錯誤: {str(e)}", level="error")
        if 'task_id' in locals():
            task_ref = db.query(models.ScrapeTask).filter(models.ScrapeTask.id == task_id).first()
            if task_ref:
                task_ref.status = "Failed"
                task_ref.error_message = f"系統錯誤: {str(e)[:200]}"
                task_ref.completed_at = datetime.utcnow()
                db.commit()
            add_task_log(db, task_id, "error", f"❌ 任務執行失敗: {str(e)[:100]}")
        return {"added": 0, "synced": 0, "skipped": 0, "error": str(e)}
    finally:
        db.close()
