"""
Simplified scraper using search engine dorking.
Scrapes company names + emails directly without AI classification.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import asyncio
import models
from database import SessionLocal
from logger import add_log
from email_finder import find_emails_for_company, guess_domain_from_name, check_mx_record

def scrape_simple(market: str = "US", pages: int = 3):
    """
    Background task: scrape companies using Yahoo search dorking.
    Only extracts company_name + email_candidates.
    """
    db = SessionLocal()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    # Auto parts keywords
    keywords = [
        "auto parts manufacturer",
        "car parts supplier",
        "automotive components maker",
        "vehicle parts factory",
        "truck parts manufacturer"
    ]
    
    stats = {"found": 0, "saved": 0, "skipped": 0}
    
    for keyword in keywords:
        add_log(f"🔍 [簡化爬蟲] 關鍵字: {keyword}")
        
        # Use Yahoo search
        query = f"{keyword} site:yellowpages.com"
        url = f"https://search.yahoo.com/search?p={query}&nso=zone&ntf=zone&ntt=zone"
        
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                add_log(f"⚠️ [Yahoo] Blocked: {resp.status_code}")
                time.sleep(5)
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = soup.find_all('div', class_='algo')
            
            if not results:
                results = soup.find_all('li', class_='algo')
            
            if not results:
                add_log(f"📭 [Yahoo] No results for {keyword}")
                time.sleep(3)
                continue
            
            add_log(f"🎯 [Yahoo] Found {len(results)} results")
            
            for result in results[:5]:  # Limit per keyword
                title_elem = result.find('h3') or result.find('a')
                if not title_elem:
                    continue
                    
                company_name = title_elem.text.strip()
                
                # Clean company name
                for sep in [' - YellowPages', ' | YellowPages', ' - SuperPages', ' | SuperPages']:
                    company_name = company_name.replace(sep, '')
                
                if len(company_name) < 3:
                    continue
                
                stats["found"] += 1
                
                # Check if already exists
                existing = db.query(models.Lead).filter(
                    models.Lead.company_name == company_name
                ).first()
                
                if existing:
                    stats["skipped"] += 1
                    continue
                
                # Try to find email
                email_info = asyncio.run(find_emails_for_company(company_name))
                
                lead = models.Lead(
                    company_name=company_name,
                    website_url=email_info.get("domain"),
                    domain=email_info.get("domain"),
                    email_candidates=", ".join(email_info.get("emails", [])) if email_info.get("emails") else None,
                    mx_valid=1 if email_info.get("mx_valid") else 0,
                    ai_tag="AUTO-UNKNOWN",
                    status="Scraped"
                )
                db.add(lead)
                stats["saved"] += 1
                
                if stats["saved"] % 5 == 0:
                    db.commit()
                    add_log(f"📊 [進度] 已儲存 {stats['saved']} 筆")
                
                time.sleep(2)
            
            time.sleep(5)
            
        except Exception as e:
            add_log(f"❌ [錯誤] {keyword}: {e}")
    
    db.commit()
    db.close()
    add_log(f"🏁 [完成] 找到:{stats['found']} 新增:{stats['saved']} 跳過:{stats['skipped']}")


if __name__ == "__main__":
    scrape_simple()
