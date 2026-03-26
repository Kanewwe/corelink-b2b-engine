"""
Isolation Pool & Category Verification Script
1. 驗證資料表結構
2. 驗證全域池同步邏輯
3. 驗證產業別分類標籤
"""

import sys
import os
import models
from database import SessionLocal, engine
from scrape_utils import sync_from_global_pool, save_to_global_pool
from classifier import classify_lead

def verify_all():
    db = SessionLocal()
    print("🚀 Running v2.7 Verification...")

    # 1. 測試分類器
    test_desc = "We manufacture custom wiring harnesses and electrical cables for industrial machinery."
    cat = classify_lead("ACME Electronics", test_desc)
    print(f"✅ Classifier Check: {cat['Tag']} (Expected: ELEC-CABLE)")
    
    test_desc_2 = "Leading provider of plastic injection molding and custom resin parts."
    cat_2 = classify_lead("PlastiCorp", test_desc_2)
    print(f"✅ Classifier Check: {cat_2['Tag']} (Expected: CHEM-MOLDING or CHEM-PLASTIC)")

    # 2. 測試全域池存儲
    lead_data = {
        "company_name": "Antigravity Global",
        "domain": "antigravity.ai",
        "website_url": "https://antigravity.ai",
        "description": "AI-powered aerospace components manufacturing.",
        "ai_tag": "IND-MANUFACTURING",
        "source": "manual_verification"
    }
    
    # 確保清除舊數據 (Local SQLite 測試)
    db.query(models.GlobalLead).filter(models.GlobalLead.domain == "antigravity.ai").delete()
    db.query(models.Lead).filter(models.Lead.domain == "antigravity.ai").delete()
    db.commit()

    print("📡 Saving to Global Pool...")
    save_to_global_pool(db, lead_data)
    
    # 3. 測試跨用戶同步
    USER_ID_A = 999
    print(f"🔄 Syncing to User {USER_ID_A}...")
    lead, is_new = sync_from_global_pool(db, USER_ID_A, domain="antigravity.ai")
    
    if lead and is_new:
        print(f"🎉 SUCCESS: Lead synced from Global Pool to User {USER_ID_A}")
        print(f"   Name: {lead.company_name}")
        print(f"   Tag: {lead.ai_tag}")
        print(f"   Link: global_id={lead.global_id}")
    else:
        print("❌ FAILED: Lead not synced correctly.")

    db.close()

if __name__ == "__main__":
    verify_all()
