"""
製造商模式 (Manufacturer Mode)
專為搜尋中小型 B2B 製造商 / 採購商設計
資料來源：Google Custom Search + Thomasnet + 備援 Dork
"""

import re
import asyncio
import httpx
import random
import os
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from logger import add_log
import models
from database import SessionLocal

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
# 注意：這裡使用 GOOGLE_CSE_ID 配合 free_email_hunter 的命名慣例
GOOGLE_CSE_ID  = os.getenv("GOOGLE_CSE_ID", "")

# ── 真實瀏覽器 UA ──────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# ── 針對製造商的 B2B 修飾詞 ──────────────
B2B_SUFFIXES = [
    "manufacturer",
    "manufacturing company",
    "OEM supplier",
    "wholesale distributor",
    "B2B supplier",
    "factory direct",
    "industrial supplier",
]

# ── 公司規模過濾詞（排除大型跨國企業）──
ENTERPRISE_BLACKLIST = [
    "bosch", "siemens", "honeywell", "3m", "johnson", "ge ", "ford",
    "toyota", "samsung", "lg ", "apple", "amazon", "walmart",
]

# ══════════════════════════════════════════
# Step 1：把使用者輸入的關鍵字轉成製造商搜尋詞
# ══════════════════════════════════════════

def build_manufacturer_queries(keyword: str, market: str = "US") -> List[str]:
    """
    把關鍵字轉成針對中小型製造商的精準搜尋詞
    例如：'car battery' → ['car battery manufacturer SME', ...]
    """
    queries = []
    
    # 組合 1：直接加 manufacturer + 中小企業修飾
    queries.append(f"{keyword} manufacturer small medium enterprise")
    queries.append(f"{keyword} OEM supplier factory")
    queries.append(f"{keyword} manufacturing company contact email")
    
    # 組合 2：針對採購尋找
    queries.append(f"{keyword} wholesale supplier B2B procurement")
    
    # 組合 3：地區限定（只限美國中小企業）
    if market == "US":
        queries.append(f"{keyword} manufacturer USA small business")
        queries.append(f"site:thomasnet.com {keyword}")          # Thomasnet 是美國 B2B 目錄
        queries.append(f"site:manta.com {keyword} manufacturer") # Manta 是中小企業目錄
    elif market == "EU":
        queries.append(f"{keyword} manufacturer Europe SME contact")
        queries.append(f"site:europages.com {keyword}")
    elif market == "TW":
        queries.append(f"{keyword} 製造商 中小企業 聯絡")
        queries.append(f"site:taiwantrade.com {keyword}")
    
    add_log(f"📋 製造商模式：產生 {len(queries)} 個搜尋查詢")
    return queries


# ══════════════════════════════════════════
# Step 2a：Google Custom Search API 搜尋
# ══════════════════════════════════════════

async def search_via_google_cse(
    query: str,
    pages: int = 1
) -> List[Dict]:
    """
    使用 Google Custom Search API 找製造商公司
    免費 100 次/日，最穩定的來源
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        # add_log("⚠️ 未設定 GOOGLE_API_KEY，跳過 Google CSE")
        return []

    results = []
    
    async with httpx.AsyncClient(timeout=15) as client:
        for page in range(pages):
            try:
                resp = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": GOOGLE_API_KEY,
                        "cx": GOOGLE_CSE_ID,
                        "q": query,
                        "num": 10,
                        "start": page * 10 + 1,
                        "gl": "us",           # 地區偏向美國
                        "lr": "lang_en",
                    }
                )
                
                if resp.status_code != 200:
                    add_log(f"⚠️ Google CSE 回應 {resp.status_code}")
                    break
                
                data = resp.json()
                items = data.get("items", [])
                
                for item in items:
                    company = extract_company_from_result(item)
                    if company:
                        results.append(company)
                
                add_log(f"  📄 Google CSE 第{page+1}頁：取得 {len(items)} 筆")
                await asyncio.sleep(0.5)

            except Exception as e:
                add_log(f"⚠️ Google CSE 錯誤：{str(e)[:50]}")
                break
    
    return results


def extract_company_from_result(item: Dict) -> Optional[Dict]:
    """從 Google 搜尋結果提取公司資訊"""
    url = item.get("link", "")
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    
    domain = extract_domain(url)
    if not domain:
        return None
    
    # 過濾掉黃頁、評論網站、大型平台
    skip_domains = [
        "yelp.com", "yellowpages.com", "google.com", "linkedin.com",
        "facebook.com", "wikipedia.org", "amazon.com", "alibaba.com",
        "made-in-china.com", "thomasnet.com", "manta.com"
    ]
    if any(skip in domain for skip in skip_domains):
        return None
    
    # 過濾大型跨國企業
    title_lower = title.lower()
    if any(name in title_lower for name in ENTERPRISE_BLACKLIST):
        return None
    
    # 清理公司名稱
    company_name = clean_company_name(title)
    if len(company_name) < 2:
        return None
    
    return {
        "company_name": company_name,
        "website": url,
        "domain": domain,
        "snippet": snippet[:200],
        "source": "google_cse",
    }


# ══════════════════════════════════════════
# Step 2b：Thomasnet 爬取（美國 B2B 目錄）
# ══════════════════════════════════════════

# ── ScraperAPI Key ──────────────────────────
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "c38c4f60be876f7dfd12178cc83b24a0")

async def search_thomasnet(keyword: str, pages: int = 1) -> List[Dict]:
    """
    Thomasnet 是美國最大的 B2B 製造商目錄
    使用 ScraperAPI 避免被擋
    """
    results = []
    
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, pages + 1):
            try:
                target_url = f"https://www.thomasnet.com/search/?searchTerm={quote_plus(keyword)}&pg={page}"
                
                # 使用 ScraperAPI
                params = {
                    "api_key": SCRAPER_API_KEY,
                    "url": target_url,
                    "render": "true",    # Thomasnet 需要 JS
                    "premium": "true"    # 住宅代理更穩
                }
                
                resp = await client.get("http://api.scraperapi.com", params=params)
                
                if resp.status_code != 200:
                    add_log(f"⚠️ Thomasnet ScraperAPI 回應 {resp.status_code}")
                    break
                
                soup = BeautifulSoup(resp.text, "lxml")
                
                # Thomasnet 的公司卡片 selector (可能隨時變動，故多列幾種)
                company_cards = soup.select(".profile-card, .supplier-card, [data-testid='company-card'], .search-result")
                
                for card in company_cards:
                    name_el = card.select_one(".company-name, h2, h3, .title")
                    link_el = card.select_one("a[href*='www.']") # 尋找外部官網連結
                    
                    if not name_el:
                        continue
                    
                    company_name = name_el.get_text(strip=True)
                    website = ""
                    domain = ""
                    
                    if link_el:
                        href = link_el.get("href", "")
                        # 處理 Thomasnet 的跳轉連結或直接連結
                        if "http" in href:
                            website = href
                            domain = extract_domain(href)
                    
                    if company_name and len(company_name) > 2:
                        results.append({
                            "company_name": company_name,
                            "website": website,
                            "domain": domain,
                            "source": "thomasnet",
                        })
                
                add_log(f"  🏭 Thomasnet：取得 {len(results)} 筆")
                # ScraperAPI 已經處理了控速，我們只需小休
                await asyncio.sleep(1)
                
            except Exception as e:
                add_log(f"⚠️ Thomasnet 錯誤：{str(e)[:50]}")
                break
    
    return results


# ══════════════════════════════════════════
# Step 2c：備援 — Bing 搜尋（不被封鎖）
# ══════════════════════════════════════════

async def search_via_bing(query: str) -> List[Dict]:
    """
    Bing 搜尋作為 Google CSE 的備援
    不需要 API Key，但需要控速
    """
    results = []
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(
                "https://www.bing.com/search",
                params={"q": query, "count": 15, "first": 1}
            )
            
            if resp.status_code != 200:
                return []
            
            soup = BeautifulSoup(resp.text, "lxml")
            
            # Bing 搜尋結果 selector
            for result in soup.select(".b_algo"):
                title_el = result.select_one("h2 a")
                snippet_el = result.select_one(".b_caption p")
                
                if not title_el:
                    continue
                
                url = title_el.get("href", "")
                title = title_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                domain = extract_domain(url)
                
                skip_domains = [
                    "yelp.com", "yellowpages.com", "google.com",
                    "facebook.com", "wikipedia.org", "amazon.com",
                    "linkedin.com", "instagram.com"
                ]
                if not domain or any(s in domain for s in skip_domains):
                    continue
                
                results.append({
                    "company_name": clean_company_name(title),
                    "website": url,
                    "domain": domain,
                    "snippet": snippet[:200],
                    "source": "bing_search",
                })
            
            add_log(f"  🔵 Bing：取得 {len(results)} 筆")
            await asyncio.sleep(random.uniform(3, 5))
            
        except Exception as e:
            add_log(f"⚠️ Bing 錯誤：{str(e)[:50]}")
    
    return results


# ══════════════════════════════════════════
# Step 3：主入口 — 製造商模式探勘
# ══════════════════════════════════════════

async def manufacturer_mine(
    keyword: str,
    market: str = "US",
    pages: int = 3,
    user_id: int = None
) -> Dict:
    """
    製造商模式主入口
    整合多來源搜尋 + 三層 Email 策略
    """
    from free_email_hunter import find_emails_free
    from models import Lead
    
    db = SessionLocal()
    add_log(f"🏭 [製造商模式] 開始探勘：{keyword} | 市場：{market}")
    
    # ── Step 1：建立搜尋查詢 ──────────────────
    queries = build_manufacturer_queries(keyword, market)
    
    # ── Step 2：多來源搜尋公司名單 ───────────
    all_companies = []
    seen_domains = set()
    
    # 策略：Google CSE (優先) -> 如果失敗或沒結果 -> Bing
    for i, query in enumerate(queries[:4]):
        add_log(f"🔍 搜尋 [{i+1}/4]：{query[:60]}")
        
        current_results = []
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            current_results = await search_via_google_cse(query, pages=1)
        
        # 如果 Google 沒結果或 API 失敗，立即使用 Bing 備援
        if not current_results:
            add_log(f"  🔄 Google 無法使用，呼叫 Bing 備援...")
            current_results = await search_via_bing(query)
        
        # 去重
        for co in current_results:
            domain = co.get("domain", "")
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_companies.append(co)
            elif not domain and co.get("company_name"):
                # 如果沒有 domain 但有公司名，也先放進去，後面再找
                all_companies.append(co)
        
        await asyncio.sleep(1)
    
    # 補充 Thomasnet（針對美國市場且結果不足時）
    if market == "US" and len(all_companies) < 15:
        add_log(f"🏭 結果不足，嘗試 Thomasnet 目錄搜尋...")
        thomas_results = await search_thomasnet(keyword, pages=1)
        for co in thomas_results:
            domain = co.get("domain", "")
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_companies.append(co)
            elif not domain and co["company_name"] not in [c["company_name"] for c in all_companies]:
                all_companies.append(co)
    
    add_log(f"📊 共找到 {len(all_companies)} 家不重複公司")
    
    if not all_companies:
        add_log("❌ 製造商模式：找不到任何公司，請換關鍵字")
        db.close()
        return {"added": 0, "skipped": 0, "failed": 0}
    
    # ── Step 3：逐家進行三層 Email 探勘 ──────
    stats = {"added": 0, "skipped": 0, "failed": 0}
    
    for co in all_companies[:30]:  # 每次最多處理 30 家
        company_name = co["company_name"]
        website = co.get("website", "")
        domain_found = co.get("domain", "")
        
        add_log(f"🏢 [{company_name}]")
        
        try:
            # 去除重複
            if domain_found:
                existing = db.query(Lead).filter(
                    Lead.domain == domain_found,
                    Lead.user_id == user_id
                ).first()
                if existing:
                    add_log(f"  ⏭️ 已存在，跳過")
                    stats["skipped"] += 1
                    continue

            # 三層 Email 策略
            if not domain_found:
                 # 如果沒有 domain，嘗試自動發現
                 from free_email_hunter import auto_discover_domain
                 domain_found = await auto_discover_domain(company_name)
            
            if not domain_found:
                add_log(f"  ⚠️ 無法找到 domain，跳過")
                stats["failed"] += 1
                continue

            # 調用 email_hunter
            email_result = await find_emails_free(domain_found, company_name)
            
            best_email_obj = email_result.get("best_email")
            all_emails = [e["email"] for e in email_result.get("emails", [])]
            
            # 整理 Email
            email = best_email_obj["email"] if best_email_obj else f"info@{domain_found}"
            email_role = best_email_obj.get("role", "unknown") if best_email_obj else "unknown"
            
            # 產業分類（從 snippet 快速判斷）
            industry = classify_industry(co.get("snippet", "") + " " + company_name)
            
            # 寫入資料庫
            lead = Lead(
                user_id       = user_id,
                company_name  = company_name,
                website_url   = website,
                domain        = domain_found,
                contact_email = email,
                email_candidates = ", ".join(all_emails) if all_emails else email,
                ai_tag        = industry,
                status        = "Scraped",
                assigned_bd   = "Manufacturer-Mode",
                extracted_keywords = keyword,
                scrape_location = market
            )
            db.add(lead)
            db.commit()
            
            role_icon = {"procurement": "🎯", "owner": "👔", "sales": "💼"}.get(email_role, "📧")
            add_log(f"  ✅ 新增：{email} {role_icon}[{email_role}] | 產業：{industry}")
            stats["added"] += 1
            
        except Exception as e:
            add_log(f"  ❌ 處理錯誤：{str(e)[:60]}")
            stats["failed"] += 1
        
        await asyncio.sleep(random.uniform(1.0, 2.0))
    
    db.close()
    add_log(f"\n🏁 製造商模式完成：新增 {stats['added']} | 跳過 {stats['skipped']} | 失敗 {stats['failed']}")
    return stats


# ══════════════════════════════════════════
# 輔助函數
# ══════════════════════════════════════════

INDUSTRY_KEYWORDS = {
    "Auto Parts":     ["auto", "car", "vehicle", "automotive", "motor"],
    "Cable & Wire":   ["cable", "wire", "harness", "electrical wiring"],
    "Electronics":    ["electronic", "circuit", "PCB", "semiconductor"],
    "Plastics":       ["plastic", "injection molding", "polymer", "resin"],
    "Metal Fab":      ["metal", "steel", "aluminum", "fabrication", "casting"],
    "Machinery":      ["machine", "equipment", "industrial", "CNC"],
    "Chemical":       ["chemical", "compound", "material", "coating"],
    "Textile":        ["textile", "fabric", "apparel", "garment"],
    "Food & Bev":     ["food", "beverage", "packaging", "processing"],
}

def classify_industry(text: str) -> str:
    text_lower = text.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return industry
    return "Manufacturing"

def clean_company_name(title: str) -> str:
    """清理公司名稱"""
    # 移除常見後綴
    title = re.sub(r'\s*[-|]\s*.+$', '', title)
    title = re.sub(r'\s*(LLC|Inc|Corp|Ltd|Co\.?|Company|Manufacturer)\.?\s*$', '', title, flags=re.IGNORECASE)
    return title.strip()

def extract_domain(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        if "://" not in url:
            url = f"https://{url}"
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None
    except Exception:
        return None

if __name__ == "__main__":
    # 測試腳本
    async def test():
        await manufacturer_mine("car battery", "US", 1, 1)
    
    asyncio.run(test())
