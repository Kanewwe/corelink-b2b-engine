"""
Linkora Backend - Startup Jobs (v3.6)
解耦自 main.py，包含所有資料庫初始化與管理員確認邏輯
"""
import os
from database import get_db
import models
from logger import add_log


def init_default_plans():
    """Initialize default subscription plans if they don't exist"""
    db = next(get_db())
    try:
        existing = db.query(models.Plan).first()
        if not existing:
            free_plan = models.Plan(
                name="free",
                display_name="免費方案",
                price_monthly=0,
                price_yearly=0,
                max_customers=50,
                max_emails_month=10,
                max_templates=1,
                max_autominer_runs=3,
                feature_ai_email=False,
                feature_attachments=False,
                feature_click_track=False,
                feature_open_track=True,
                feature_hunter_io=False,
                feature_api_access=False,
                feature_csv_import=False
            )
            db.add(free_plan)

            pro_plan = models.Plan(
                name="pro",
                display_name="專業方案",
                price_monthly=890,
                price_yearly=8900,
                max_customers=500,
                max_emails_month=500,
                max_templates=10,
                max_autominer_runs=30,
                feature_ai_email=True,
                feature_attachments=True,
                feature_click_track=True,
                feature_open_track=True,
                feature_hunter_io=True,
                feature_api_access=False,
                feature_csv_import=True
            )
            db.add(pro_plan)

            enterprise_plan = models.Plan(
                name="enterprise",
                display_name="企業方案",
                price_monthly=2990,
                price_yearly=29900,
                max_customers=-1,
                max_emails_month=-1,
                max_templates=-1,
                max_autominer_runs=-1,
                feature_ai_email=True,
                feature_attachments=True,
                feature_click_track=True,
                feature_open_track=True,
                feature_hunter_io=True,
                feature_api_access=True,
                feature_csv_import=True
            )
            db.add(enterprise_plan)
            db.commit()
            add_log("✅ 預設方案初始化完成")
    except Exception as e:
        add_log(f"⚠️ 方案初始化失敗: {e}")
    finally:
        db.close()


def ensure_admin_exists():
    """Ensure at least one admin account exists"""
    db = next(get_db())
    try:
        admin_email = "admin@linkora.com"
        admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin:
            print(f"🚀 Bootstrapping Admin: {admin_email}...")
            admin = models.User(
                email=admin_email,
                name="Linkora Admin",
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(admin)

        target_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        admin.set_password(target_pass)
        admin.role = "admin"
        db.commit()
        print("✅ Admin credentials ensured.")
    except Exception as e:
        print(f"⚠️ Admin bootstrap failed: {e}")
    finally:
        db.close()


def run_startup_tasks():
    """
    Main entrypoint for all startup background tasks.
    Called from main.py lifespan in a daemon thread.
    """
    from database import init_db
    from migrations import run_migrations
    from industry_tags import init_industry_tags

    try:
        init_db()
        run_migrations()
        init_default_plans()
        ensure_admin_exists()
        # v3.7.29: 初始化行業標籤
        db = next(get_db())
        try:
            init_industry_tags(db)
        except Exception as e:
            add_log(f"⚠️ [Industry] Init error: {str(e)}")
        finally:
            db.close()
        add_log("🚀 [System] All startup tasks completed in background (v3.7.29)")
    except Exception as e:
        add_log(f"🚨 [System] Startup task error: {str(e)}")
