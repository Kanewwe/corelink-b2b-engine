"""
Scraper Engine - 直接爬取黃頁網站
取代原本透過 Yahoo Search 的間接方式
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Optional
from logger import add_log

# 黃頁網站設定
DIRECTORY_CONFIGS = {
    "US": [
        {
            "domain": "yellowpages.com",
            "search_url": "https://www.yellowpages.com/search?search_terms={keyword}&geo_location_terms={location}",
            "result_selector": "div.result",
            "name_selector": "a.business-name span",
            "phone_selector": "div.phones.phone.primary",
            "address_selector": "div.street-address",
            "city_selector": "div.locality",
            "website_selector": "a.track-visit-website",
            "category_selector": "div.categories a",
        },
        {
            "domain": "yelp.com",
            "search_url": "https://www.yelp.com/search?find_desc={keyword}&find_loc={location}",
            "result_selector": "li[class*='business-name']",
            "name_selector": "a.css-1m051bw",
            "phone_selector": None,  # Yelp 需進入詳情頁
            "website_selector": "a[href*='biz_redir']",
            "category_selector": "span.css-chan6m",
        }
    ],
    "EU": [
        {
            "domain": "yell.com",
            "search_url": "https://www.yell.com/ucs/UcsSearchAction.do?keywords={keyword}&location={location}",
            "result_selector": "article.businessCapsule",
            "name_selector": "a.businessCapsule__title",
            "phone_selector": "span.phone__number",
            "address_selector": "span.businessCapsule__address",
            "website_selector": "a.businessCapsule__website",
            "category_selector": "ul.businessCapsule__categories li",
        }
    ]
}

# 隨機 User-Agent（反爬蟲）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

def get_headers() -> dict:
    """產生隨機 Headers"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def scrape_directory(config: dict, keyword: str, location: str = "United States", max_pages: int = 3) -> List[Dict]:
    """
    直接爬取目錄網站的搜尋結果頁
    不再透過 Yahoo Search
    """
    companies = []
    
    for page in range(1, max_pages + 1):
        url = config["search_url"].format(
            keyword=requests.utils.quote(keyword),
            location=requests.utils.quote(location)
        )
        
        if page > 1:
            url += f"&page={page}"
        
        try:
            add_log(f"  🌐 Requesting: {url[:60]}...")
            resp = requests.get(url, headers=get_headers(), timeout=20)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'lxml')
                results = soup.select(config["result_selector"])
                
                if not results:
                    add_log(f"  📉 No results found on page {page}")
                    break
                
                for item in results:
                    company = extract_company_data(item, config)
                    if company:
                        companies.append(company)
                
                add_log(f"  ✅ Page {page}: {len(results)} results")
                
            elif resp.status_code == 429:
                # Rate limited - exponential backoff
                wait = 30 * page
                add_log(f"  ⚠️ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                add_log(f"  ❌ Status {resp.status_code}")
                break
            
            # 隨機延遲，模擬人類行為
            time.sleep(random.uniform(3, 7))
            
        except Exception as e:
            add_log(f"  ❌ Error: {str(e)}")
            break
    
    return companies

def extract_company_data(item, config: dict) -> Optional[Dict]:
    """從單個結果區塊萃取公司資料"""
    try:
        name_el = item.select_one(config["name_selector"])
        if not name_el:
            return None
        
        name = name_el.get_text(strip=True)
        if len(name) < 2:
            return None
        
        # 電話
        phone = ""
        if config.get("phone_selector"):
            phone_el = item.select_one(config["phone_selector"])
            phone = phone_el.get_text(strip=True) if phone_el else ""
        
        # 地址
        address = ""
        if config.get("address_selector"):
            addr_el = item.select_one(config["address_selector"])
            address = addr_el.get_text(strip=True) if addr_el else ""
        
        # 城市
        city = ""
        if config.get("city_selector"):
            city_el = item.select_one(config["city_selector"])
            city = city_el.get_text(strip=True) if city_el else ""
        
        # 網站
        website = ""
        if config.get("website_selector"):
            web_el = item.select_one(config["website_selector"])
            website = web_el.get("href", "") if web_el else ""
        
        # 產業類別
        categories = []
        if config.get("category_selector"):
            cats = item.select(config["category_selector"])
            categories = [c.get_text(strip=True) for c in cats[:5]]
        
        return {
            "company_name": name,
            "phone": phone,
            "address": address,
            "city": city,
            "website_url": website,
            "categories": ", ".join(categories),
            "source": config["domain"]
        }
    except Exception as e:
        return None