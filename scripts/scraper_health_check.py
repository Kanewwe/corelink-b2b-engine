import asyncio
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import models
from database import SessionLocal
from manufacturer_miner import manufacturer_mine
from scrape_simple import scrape_simple
from free_email_hunter import find_emails_free

async def test_scrapers():
    print(f"🚀 Linkora v3.1.8-resilience Scraper Health Check")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    db = SessionLocal()
    admin = db.query(models.User).filter(models.User.id == 1).first()
    if not admin:
        print("❌ Error: Admin user (ID 1) not found in database.")
        return

    report = {
        "timestamp": datetime.now().isoformat(),
        "modes": {}
    }

    # 1. Test Mode: Thomasnet (Manufacturer)
    print("🔎 Testing Mode: Manufacturer (Thomasnet)...")
    try:
        # We use a small result set and 1 page for speed
        res = await manufacturer_mine("metal stamps", market="US", pages=1, user_id=admin.id)
        report["modes"]["manufacturer"] = {
            "status": "Success" if res.get("added", 0) + res.get("synced", 0) > 0 else "Warn (0 items)",
            "details": res
        }
    except Exception as e:
        report["modes"]["manufacturer"] = {"status": "Failed", "error": str(e)}

    # 2. Test Mode: Yellow Pages (Simple)
    print("🔎 Testing Mode: YellowPages (Simple)...")
    try:
        # Running in a blocking way as per scrape_simple signature
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: scrape_simple(market="US", pages=1, keywords=["plastic"], user_id=admin.id))
        report["modes"]["yellowpages"] = {
            "status": "Success" if res.get("saved", 0) + res.get("synced", 0) > 0 else "Warn (0 items)",
            "details": res
        }
    except Exception as e:
        report["modes"]["yellowpages"] = {"status": "Failed", "error": str(e)}

    # 3. Test Mode: Free Email Hunter (Direct/Proxy)
    print("🔎 Testing Mode: Free Email Hunter...")
    try:
        test_domain = "apple.com" # Reliable test
        res = await find_emails_free(test_domain, company_name="Apple Inc", user_id=admin.id)
        report["modes"]["free_email"] = {
            "status": "Success" if res.get("emails") else "Warn (No emails)",
            "emails_found": len(res.get("emails", [])),
            "best_email": res.get("best_email", {}).get("email")
        }
    except Exception as e:
        report["modes"]["free_email"] = {"status": "Failed", "error": str(e)}

    # Save Report
    report_path = os.path.join(os.path.dirname(__file__), 'scraper_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)

    print("-" * 50)
    print(f"📊 Health Check Complete. Report saved to: {report_path}")
    
    # Summary Table
    print("\n| Mode | Status | Details |")
    print("| :--- | :--- | :--- |")
    for mode, data in report["modes"].items():
        status_icon = "✅" if "Success" in data["status"] else "⚠️" if "Warn" in data["status"] else "❌"
        print(f"| {mode.capitalize()} | {status_icon} {data['status']} | {data.get('details') or data.get('error') or data.get('emails_found')} |")

    db.close()

if __name__ == "__main__":
    asyncio.run(test_scrapers())
