
import psycopg2

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def test():
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        
        cur.execute("SELECT current_user, current_database()")
        u, d = cur.fetchone()
        print(f"User: {u}, DB: {d}")
        
        print("Testing CREATE TABLE uat.test_manual...")
        cur.execute("CREATE TABLE IF NOT EXISTS uat.test_manual (id serial primary key, note text)")
        conn.commit()
        print("Commit successful.")
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'uat'")
        print(f"UAT Tables after manual create: {[t[0] for t in cur.fetchall()]}")
        
        # Check permissions on the schema
        cur.execute("SELECT has_schema_privilege(%s, 'uat', 'CREATE')", (u,))
        print(f"Has CREATE on uat: {cur.fetchone()[0]}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test()
