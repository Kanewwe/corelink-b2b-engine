
import psycopg2
import os

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def sync():
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        
        print("Ensuring UAT schema tables exist...")
        # We assume init_db is running on Render, but let's be safe
        cur.execute("CREATE SCHEMA IF NOT EXISTS uat")
        
        # 1. Copy Users (if not exists)
        print("Syncing Users...")
        cur.execute("SELECT id, email, password_hash, name, role, is_active, is_verified FROM public.users")
        users = cur.fetchall()
        for u in users:
            cur.execute("SELECT id FROM uat.users WHERE email = %s", (u[1],))
            if not cur.fetchone():
                cur.execute("INSERT INTO uat.users (id, email, password_hash, name, role, is_active, is_verified) VALUES (%s, %s, %s, %s, %s, %s, %s)", u)
        
        # 2. Copy Scrape Tasks (if not exists)
        print("Syncing Scrape Tasks...")
        cur.execute("SELECT id, user_id, market, keywords, miner_mode, status, leads_found, started_at FROM public.scrape_tasks")
        tasks = cur.fetchall()
        for t in tasks:
            cur.execute("SELECT id FROM uat.scrape_tasks WHERE id = %s", (t[0],))
            if not cur.fetchone():
                cur.execute("INSERT INTO uat.scrape_tasks (id, user_id, market, keywords, miner_mode, status, leads_found, started_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", t)
        
        conn.commit()
        print("✅ Sync successful!")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync()
