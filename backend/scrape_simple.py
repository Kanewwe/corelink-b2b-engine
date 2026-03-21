"""
Simplified scraper - Test version with sample data.
Uses hardcoded sample auto parts companies for testing.
"""

import models
from database import SessionLocal
from logger import add_log

# Sample auto parts companies for testing
SAMPLE_COMPANIES = [
    {"name": "AutoZone", "domain": "autozone.com"},
    {"name": "O'Reilly Auto Parts", "domain": "oreillyauto.com"},
    {"name": "Advance Auto Parts", "domain": "shop.advanceautoparts.com"},
    {"name": "NAPA Auto Parts", "domain": "napaonline.com"},
    {"name": "Pep Boys", "domain": "pepboys.com"},
    {"name": "Bosch Auto Parts", "domain": "bosch-automotive.com"},
    {"name": "Denso Corporation", "domain": "denso.com"},
    {"name": "Valeo North America", "domain": "valeo.com"},
    {"name": "Magna International", "domain": "magna.com"},
    {"name": "Lear Corporation", "domain": "lear.com"},
    {"name": "Aptiv PLC", "domain": "aptiv.com"},
    {"name": "BorgWarner Inc", "domain": "borgwarner.com"},
    {"name": "Delphi Technologies", "domain": "delphi.com"},
    {"name": "Continental AG", "domain": "continental.com"},
    {"name": "ZF Friedrichshafen", "domain": "zf.com"},
    {"name": "Federal-Mogul", "domain": "federalmogul.com"},
    {"name": "Gates Corporation", "domain": "gates.com"},
    {"name": "Honeywell Automotive", "domain": "honeywell.com"},
    {"name": "Dorman Products", "domain": "dormanproducts.com"},
    {"name": "Standard Motor Products", "domain": "smpcorp.com"},
]

def scrape_simple(market: str = "US", pages: int = 3):
    """
    Test version: Import sample companies and find emails.
    """
    db = SessionLocal()
    stats = {"saved": 0, "skipped": 0}
    
    add_log(f"🔍 [簡化爬蟲] 開始匯入測試資料 (market={market})")
    
    for company in SAMPLE_COMPANIES:
        name = company["name"]
        domain = company["domain"]
        
        # Check if exists
        existing = db.query(models.Lead).filter(
            models.Lead.company_name == name
        ).first()
        
        if existing:
            stats["skipped"] += 1
            add_log(f"⏭ [跳過] {name} - 已存在")
            continue
        
        # Create lead with test emails
        email = f"info@{domain}"
        
        lead = models.Lead(
            company_name=name,
            website_url=f"https://{domain}",
            domain=domain,
            email_candidates=email,
            mx_valid=1,
            ai_tag="AUTO-UNKNOWN",
            status="Scraped"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        stats["saved"] += 1
        add_log(f"✅ [匯入] {name} -> {email}")
    
    db.close()
    add_log(f"🏁 [完成] 新增:{stats['saved']} 跳過:{stats['skipped']}")
    return stats


if __name__ == "__main__":
    scrape_simple()
