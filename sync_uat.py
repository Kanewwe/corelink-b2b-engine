
import sys
import os
sys.path.append(os.getcwd())

from backend.database import engine, Base, SessionLocal, APP_ENV
from sqlalchemy import text
import backend.models as models

def sync_uat():
    print("🚀 Initializing UAT database...")
    
    # Force search_path to uat
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS uat"))
        conn.execute(text("SET search_path TO uat"))
        
        # Create tables
        print("Creating tables in uat...")
        Base.metadata.create_all(bind=engine)
        conn.commit()
    
    # Sync data
    db = SessionLocal()
    try:
        # Check if users exist in uat
        # Note: SessionLocal uses connect_args which includes search_path=uat (if APP_ENV=uat)
        # But here I want to be explicit.
        
        # 建立一個連線到 public 的 session 來抓資料
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("DATABASE_URL not found")
            return
            
        public_engine = create_engine(db_url, connect_args={"options": "-c search_path=public"})
        PublicSession = sessionmaker(bind=public_engine)
        public_db = PublicSession()
        
        uat_engine = create_engine(db_url, connect_args={"options": "-c search_path=uat"})
        UatSession = sessionmaker(bind=uat_engine)
        uat_db = UatSession()
        
        # 1. Sync Plans
        print("Syncing Plans...")
        plans = public_db.query(models.Plan).all()
        for p in plans:
            existing = uat_db.query(models.Plan).filter(models.Plan.id == p.id).first()
            if not existing:
                uat_db.execute(text(f"INSERT INTO uat.plans (id, name, display_name, price_monthly, price_yearly) VALUES ({p.id}, '{p.name}', '{p.display_name}', {p.price_monthly}, {p.price_yearly})"))
        uat_db.commit()
        
        # 2. Sync Admin User
        print("Syncing Users...")
        users = public_db.query(models.User).all()
        for u in users:
            existing = uat_db.query(models.User).filter(models.User.email == u.email).first()
            if not existing:
                # Use raw SQL to preserve ID
                uat_db.execute(text(f"INSERT INTO uat.users (id, email, password_hash, name, role, is_active, is_verified) VALUES ({u.id}, '{u.email}', '{u.password_hash}', '{u.name}', '{u.role}', {u.is_active}, {u.is_verified})"))
        uat_db.commit()
        
        # 3. Sync Scrape Tasks
        print("Syncing Scrape Tasks...")
        tasks = public_db.query(models.ScrapeTask).all()
        for t in tasks:
            existing = uat_db.query(models.ScrapeTask).filter(models.ScrapeTask.id == t.id).first()
            if not existing:
                uat_db.execute(text(f"INSERT INTO uat.scrape_tasks (id, user_id, market, keywords, miner_mode, status, leads_found, started_at) VALUES ({t.id}, {t.user_id}, '{t.market}', '{t.keywords}', '{t.miner_mode}', '{t.status}', {t.leads_found or 0}, '{t.started_at}')"))
        uat_db.commit()
        
        print("✅ UAT Sync Complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    sync_uat()
