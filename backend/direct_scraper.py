"""
Linkora v3.2 — Direct YellowPages Scraper
不使用 Apify actors，直接爬取 YellowPages.com
更穩定、零成本、不依賴第三方演算法
"""

import re
import time
import logging
import urllib.request
import urllib.parse
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── 瀏覽器 User-Agent ──────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def _make_request(url: str, timeout: int = 15) -> tuple:
    """
    發送 HTTP GET，自動處理 User-Agent 輪換和格式分析
    Returns: (html: str, status_code: int, response_time: float)
    """
    import random
    import time as _time
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    start_time = _time.time()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            charset = "utf-8"
            ct = resp.headers.get("Content-Type", "")
            if "charset=" in ct:
                charset = ct.split("charset=")[-1].split(";")[0].strip()
            html = resp.read().decode(charset, errors="replace")
            duration = _time.time() - start_time
            return html, status, duration
    except Exception as e:
        duration = _time.time() - start_time
        status = getattr(e, 'code', 500) if hasattr(e, 'code') else 500
        logger.warning(f"Request failed: {url} — {e} | Status: {status}")
        return None, status, duration


def _extract_emails(text: str) -> List[str]:
    """從文字中提取 email"""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    emails = re.findall(pattern, text)
    # 去重並過濾明顯垃圾郵箱
    seen = set()
    result = []
    for e in emails:
        e = e.lower()
        if e in seen:
            continue
        if any(bad in e for bad in ["noreply", "example", "test@"]):
            continue
        seen.add(e)
        result.append(e)
    return result


def _extract_phone(text: str) -> Optional[str]:
    """提取電話號碼"""
    pattern = r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
    matches = re.findall(pattern, text)
    if matches:
        phone = re.sub(r"[^\d]", "", matches[0])
        if len(phone) == 10 or (len(phone) == 11 and phone[0] == "1"):
            return phone
    return None


def _clean_name(raw: str) -> str:
    """清理公司名稱"""
    name = raw.strip()
    # 移除常見尾碼
    for suffix in [" - Yellow Pages", " | Yellowpages", " (YP)", " - Map"]:
        name = name.replace(suffix, "")
    return name.strip()


def _is_valid_business(name: str) -> bool:
    """過濾掉明顯非目標公司的記錄"""
    name_lower = name.lower()
    bad_keywords = [
        "restaurant", "cafe", "coffee", "bar ", " pub ", "pizza", "grill",
        "hotel", "inn ", "motel", "bistro", "deli", "bakery",
        "fast food", "take out", "food court",
    ]
    for kw in bad_keywords:
        if kw in name_lower:
            return False
    return True


def scrape_yellowpages(keyword: str, location: str = "United States", 
                       max_pages: int = 1, task_id: int = None) -> List[Dict]:
    """
    直接爬取 YellowPages.com 搜尋結果
    
    Args:
        keyword: 搜尋關鍵字（例：electronics manufacturer）
        location: 地點（例：United States）
        max_pages: 最大頁數（每頁約 30 筆）
        task_id: 選填，用於紀錄健康指標 (v3.4)
    
    Returns:
        List of dicts with: name, website, phone, address, emails
    """
    from scraper_utils import log_scrape_health
    results = []
    seen_domains = set()
    
    # 依頁數迭代
    for page in range(1, max_pages + 1):
        # YellowPages 搜尋 URL
        # 格式：https://www.yellowpages.com/search?search_terms=keyword&geo_location_terms=location
        params = {
            "search_terms": keyword,
            "geo_location_terms": location,
        }
        if page > 1:
            params["page"] = page
        
        search_url = "https://www.yellowpages.com/search?" + urllib.parse.urlencode(params)
        logger.info(f"🌐 Scraping page {page}: {search_url[:80]}")
        
        html, status, duration = _make_request(search_url, timeout=20)
        
        # SA v3.4: 紀錄爬取健康指標
        if task_id:
            log_scrape_health(
                task_id=task_id,
                message=f"YellowPages Page {page} scraped",
                level="success" if html else "error",
                response_time=duration,
                http_status=status,
                keyword=keyword,
                page=page
            )

        if not html:
            logger.warning(f"Failed to fetch page {page}")
            continue
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 找所有公司列表項目
        listings = soup.select("div.search-results div.result")
        if not listings:
            # 嘗試其他選擇器
            listings = soup.select("div#super.container div.result")
        if not listings:
            listings = soup.select("div.result")
        
        logger.info(f"  Found {len(listings)} listings on page {page}")
        
        if not listings:
            break
        
        for listing in listings:
            try:
                # 公司名稱
                name_elem = listing.select_one("a.business-name span")
                name = _clean_name(name_elem.get_text(strip=True)) if name_elem else ""
                
                if not name or len(name) < 2:
                    continue
                
                # 過濾
                if not _is_valid_business(name):
                    continue
                
                # 網站
                website_elem = listing.select_one("a.track-visit-cta")
                website = website_elem.get("href", "") if website_elem else ""
                if website and not website.startswith("http"):
                    website = "https://www.yellowpages.com" + website
                
                # 提取 domain
                domain = ""
                if website and "yellowpages" not in website:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(website).netloc.replace("www.", "")
                    except:
                        pass
                
                # 避免重複 domain
                if domain and domain in seen_domains:
                    logger.info(f"  ⏭️ 跳過重複: {name} ({domain})")
                    continue
                if domain:
                    seen_domains.add(domain)
                
                # 電話
                phone_elem = listing.select_one("div.phones")
                phone = _extract_phone(phone_elem.get_text(strip=True)) if phone_elem else None
                
                # 地址
                addr_elem = listing.select_one("div.street-address")
                locality_elem = listing.select_one("div.locality")
                address = ""
                if addr_elem:
                    address = addr_elem.get_text(strip=True)
                if locality_elem:
                    address += " " + locality_elem.get_text(strip=True)
                address = " ".join(address.split())
                
                # 嘗試從頁面找 email（點擊網站連結前）
                emails = []
                
                item_data = {
                    "name": name,
                    "website": website,
                    "domain": domain,
                    "phone": phone or "",
                    "address": address,
                    "emails": emails,
                    "source": "yellowpages_direct",
                    "search_keyword": keyword,
                    "search_location": location,
                    "page": page,
                }
                
                results.append(item_data)
                logger.info(f"  ✅ {name} | {domain} | {phone or '無電話'}")
                
            except Exception as e:
                logger.warning(f"  解析 listing 失敗: {e}")
                continue
        
        # 每頁之間延遲，避免被阻擋
        time.sleep(2)
    
    logger.info(f"📊 YellowPages 爬取完成：{len(results)} 筆有效結果")
    return results


def scrape_google_maps_search(keyword: str, location: str = "United States",
                              max_results: int = 30) -> List[Dict]:
    """
    使用 Google 簡單搜尋抓取公司資訊（不依賴 Google Maps API）
    搜尋格式：site:yellowpages.com "keyword" "location"
    
    這是 fallback 方案，不穩定但可行
    """
    results = []
    seen_domains = set()
    
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}+{urllib.parse.quote(location)}+company&num={max_results}"
    
    logger.info(f"🌐 Google 搜尋: {search_url[:80]}")
    html = _make_request(search_url, timeout=20)
    if not html:
        logger.warning("Google 搜尋失敗")
        return results
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 解析搜尋結果
    for result in soup.select("div.g"):
        try:
            title_elem = result.select_one("h3")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            
            link_elem = result.select_one("a[href]")
            link = link_elem.get("href", "") if link_elem else ""
            
            # 只取 YellowPages 結果
            if "yellowpages.com" not in link:
                continue
            
            # 解析公司名
            name = title.split(" - ")[0].split(" | ")[0].strip()
            if not name or len(name) < 2:
                continue
            
            if not _is_valid_business(name):
                continue
            
            item_data = {
                "name": name,
                "website": link,
                "domain": "",
                "phone": "",
                "address": "",
                "emails": [],
                "source": "google_search",
                "search_keyword": keyword,
                "search_location": location,
            }
            results.append(item_data)
            
        except Exception as e:
            continue
    
    logger.info(f"📊 Google 搜尋完成：{len(results)} 筆")
    return results


# ── 主入口：整合式爬取 ─────────────────────────────────────────
def scrape_all(keyword: str, location: str = "United States",
               max_pages: int = 1, sources: List[str] = None) -> List[Dict]:
    """
    主入口：嘗試所有可用來源
    
    Args:
        keyword: 搜尋關鍵字
        location: 地點
        max_pages: 最大頁數
        sources: 指定來源 ["yellowpages", "google"]，None=全部
    
    Returns:
        合併去重的公司列表
    """
    if sources is None:
        sources = ["yellowpages", "google"]
    
    all_results = []
    seen_domains = set()
    
    # 1. YellowPages.com 直接爬取（首選）
    if "yellowpages" in sources:
        yp_results = scrape_yellowpages(keyword, location, max_pages)
        for item in yp_results:
            if item["domain"] and item["domain"] in seen_domains:
                continue
            if item["domain"]:
                seen_domains.add(item["domain"])
            all_results.append(item)
    
    # 2. Google 搜尋（備援）
    if "google" in sources:
        g_results = scrape_google_maps_search(keyword, location, max_results=max_pages * 30)
        for item in g_results:
            if item["domain"] and item["domain"] in seen_domains:
                continue
            if item["domain"]:
                seen_domains.add(item["domain"])
            all_results.append(item)
    
    return all_results


if __name__ == "__main__":
    # 測試
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    print("=== Direct YellowPages Scraper Test ===\n")
    results = scrape_yellowpages("electronics manufacturer", "United States", max_pages=1)
    
    print(f"\n結果：{len(results)} 筆")
    for r in results[:5]:
        print(f"\n  {r['name']}")
        print(f"  website: {r['website']}")
        print(f"  phone: {r['phone']}")
        print(f"  address: {r['address']}")
