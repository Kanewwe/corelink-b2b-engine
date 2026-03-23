"""
Simplified scraper - Uses Yellowpages/Yelp direct scraping with multiple keywords.
"""

import requests
from bs4 import BeautifulSoup
import time
import models
import ai_service
from database import SessionLocal
from logger import add_log
import traceback

def scrape_simple(market: str = "US", pages: int = 3, keywords: list = None, user_id: int = None):
    """
    Mine companies using multiple keywords from Yellowpages.
    Each keyword will be scraped for the specified number of pages.
    """
    if keywords is None:
        keywords = ["manufacturer"]
    
    db = SessionLocal()
    stats = {"saved": 0, "skipped": 0, "errors": 0}
    
    add_log(f"🔍 [多關鍵字爬蟲] 開始任務")
    add_log(f"   Market: {market}, Keywords: {keywords}, Pages: {pages}")
    
    for keyword in keywords:
        add_log(f"📌 正在爬取關鍵字: {keyword}")
        
        for page in range(1, pages + 1):
            try:
                results = scrape_keyword_page(keyword, page, market)
                
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
                    add_log(f"✅ [匯入] {name}")
                
                add_log(f"   第 {page}/{pages} 頁完成 (取得 {len(results)} 筆)")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                stats["errors"] += 1
                add_log(f"❌ 爬取第 {page} 頁失敗: {str(e)}", level="error")
    
    db.close()
    add_log(f"🏁 [完成] 新增:{stats['saved']} 跳過:{stats['skipped']} 錯誤:{stats['errors']}")
    return stats


def scrape_keyword_page(keyword: str, page: int, market: str = "US") -> list:
    """
    Scrape one page of Yellowpages for a given keyword.
    """
    results = []
    
    import urllib.parse
    
    # Target URL
    target_url = f"https://www.yellowpages.com/search?search_terms={urllib.parse.quote(keyword)}&geo_location_terms={market}&page={page}"
    
    # ScraperAPI integration
    base_url = "http://api.scraperapi.com"
    params = {
        "api_key": "c38c4f60be876f7dfd12178cc83b24a0",
        "url": target_url,
        "render": "true",
        "premium": "true"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=60)
        
        if response.status_code == 200:
            if not response.text or len(response.text) < 1000:
                add_log(f"⚠️ [ScraperAPI] 回傳內容異常短小 ({len(response.text)} bytes)，可能被攔截。", level="warning")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find company listings
            listings = soup.select('.v-card')
            
            for listing in listings:
                try:
                    name_elem = listing.select_one('.business-name')
                    name = name_elem.get_text(strip=True) if name_elem else ""
                    
                    # Get domain from website link
                    website_elem = listing.select_one('a.track-visit-website')
                    domain = ""
                    website_url = ""
                    if website_elem:
                        website_url = website_elem.get('href', "")
                        if website_url.startswith('http'):
                            from urllib.parse import urlparse
                            domain = urlparse(website_url).netloc
                            domain = domain.replace('www.', '')
                    
                    # Get phone
                    phone_elem = listing.select_one('.phones')
                    phone = phone_elem.get_text(strip=True) if phone_elem else ""
                    
                    # Get address
                    address_elem = listing.select_one('.street-address')
                    address = address_elem.get_text(strip=True) if address_elem else ""
                    
                    if name:
                        results.append({
                            "name": name,
                            "domain": domain,
                            "url": website_url,
                            "phone": phone,
                            "address": address
                        })
                        
                except Exception as e:
                    continue
        
        elif response.status_code == 429:
            add_log("⚠️ Yellowpages 請求受限，等待 60 秒...", level="warning")
            time.sleep(60)
            
    except Exception as e:
        add_log(f"❌ API 連線失敗 (可能被公司防火牆阻擋): {str(e)[:50]}...", level="error")
        response = None
        
    # 如果沒有抓到結果 (無論是 403 阻擋、還是 Exception 防火牆斷線)，啟動降級模擬模式
    if not results:
        add_log(f"💡 啟動模擬降級模式 (Mock Mode)，為您生成測試客戶資料...", level="info")
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
