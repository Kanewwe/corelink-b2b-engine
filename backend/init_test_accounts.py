"""
Linkora 測試帳號初始化腳本
建立 Admin / Vendor / Member 各一組測試帳號
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
from datetime import datetime

def init_test_accounts():
    db = SessionLocal()
    
    try:
        print("🔧 建立測試帳號...")
        
        # 檢查是否已存在
        existing = db.query(models.User).filter(
            models.User.email.in_([
                'admin@linkora.com',
                'vendor@linkora.com',
                'member@linkora.com'
            ])
        ).all()
        
        if existing:
            print(f"⚠️  已存在 {len(existing)} 個測試帳號，跳過建立")
            for u in existing:
                print(f"   - {u.email} ({u.role})")
            return
        
        # 1. Admin 帳號
        admin = models.User(
            email='admin@linkora.com',
            name='系統管理員',
            company_name='Linkora Platform',
            role='admin',
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        admin.set_password('admin123')
        db.add(admin)
        
        # 2. Vendor 帳號 (簽約合作夥伴)
        vendor = models.User(
            email='vendor@linkora.com',
            name='測試廠商',
            company_name='Test Vendor Co.',
            role='vendor',
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        vendor.set_password('vendor123')
        db.add(vendor)
        
        # 3. Member 帳號 (免費版)
        member_free = models.User(
            email='member@linkora.com',
            name='測試會員',
            company_name='Test Member Co.',
            role='member',
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        member_free.set_password('member123')
        db.add(member_free)
        
        # 4. Member 帳號 (專業版)
        member_pro = models.User(
            email='member-pro@linkora.com',
            name='測試專業會員',
            company_name='Test Pro Co.',
            role='member',
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        member_pro.set_password('member123')
        db.add(member_pro)
        
        # 5. Member 帳號 (企業版)
        member_enterprise = models.User(
            email='member-enterprise@linkora.com',
            name='測試企業會員',
            company_name='Test Enterprise Co.',
            role='member',
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )
        member_enterprise.set_password('member123')
        db.add(member_enterprise)
        
        db.commit()
        
        # 建立 Subscription 記錄
        # 免費版
        free_plan = db.query(models.Plan).filter(models.Plan.name == 'free').first()
        if free_plan:
            sub_free = models.Subscription(
                user_id=member_free.id,
                plan_id=free_plan.id,
                status='active'
            )
            db.add(sub_free)
        
        # 專業版
        pro_plan = db.query(models.Plan).filter(models.Plan.name == 'pro').first()
        if not pro_plan:
            pro_plan = models.Plan(
                name='pro',
                display_name='專業版',
                price_monthly=899,
                max_customers=100,
                max_emails_month=100,
                max_templates=5,
                feature_ai_email=True,
                feature_open_track=True,
                feature_click_track=True,
                is_active=True
            )
            db.add(pro_plan)
            db.commit()
            db.refresh(pro_plan)
        
        sub_pro = models.Subscription(
            user_id=member_pro.id,
            plan_id=pro_plan.id,
            status='active'
        )
        db.add(sub_pro)
        
        # 企業版
        enterprise_plan = db.query(models.Plan).filter(models.Plan.name == 'enterprise').first()
        if not enterprise_plan:
            enterprise_plan = models.Plan(
                name='enterprise',
                display_name='企業版',
                price_monthly=2999,
                max_customers=500,
                max_emails_month=500,
                max_templates=9999,  # 無限
                feature_ai_email=True,
                feature_open_track=True,
                feature_click_track=True,
                feature_hunter_io=True,
                feature_api_access=True,
                feature_attachments=True,
                is_active=True
            )
            db.add(enterprise_plan)
            db.commit()
            db.refresh(enterprise_plan)
        
        sub_enterprise = models.Subscription(
            user_id=member_enterprise.id,
            plan_id=enterprise_plan.id,
            status='active'
        )
        db.add(sub_enterprise)
        
        db.commit()
        
        print("✅ 測試帳號建立完成！")
        print("")
        print("📋 測試帳號清單：")
        print("─────────────────────────────────────")
        print("👤 Admin (管理員)")
        print("   Email:    admin@linkora.com")
        print("   Password: admin123")
        print("")
        print("🏢 Vendor (廠商 - 無限使用)")
        print("   Email:    vendor@linkora.com")
        print("   Password: vendor123")
        print("")
        print("👤 Member Free (免費版)")
        print("   Email:    member@linkora.com")
        print("   Password: member123")
        print("   配額:     10 leads / 10 emails")
        print("")
        print("👤 Member Pro (專業版)")
        print("   Email:    member-pro@linkora.com")
        print("   Password: member123")
        print("   配額:     100 leads / 100 emails")
        print("")
        print("👤 Member Enterprise (企業版)")
        print("   Email:    member-enterprise@linkora.com")
        print("   Password: member123")
        print("   配額:     500 leads / 500 emails")
        print("─────────────────────────────────────")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 錯誤: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_test_accounts()
