
import psycopg2

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS uat")
    conn.commit()
    print("✅ UAT schema created successfully.")
    
    # Verify tables in uat
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'uat'")
    tables = cur.fetchall()
    print(f"UAT Tables: {[t[0] for t in tables]}")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
