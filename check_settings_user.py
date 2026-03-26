
import psycopg2

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def run():
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id, key, value FROM uat.system_settings")
        rows = cur.fetchall()
        for r in rows:
            print(f"User {r[0]} | Key: {r[1]} | Val: {r[2][:50]}...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
