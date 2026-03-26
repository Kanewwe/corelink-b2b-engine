
import psycopg2
import json

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def run():
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    try:
        cur.execute("SELECT value FROM uat.system_settings WHERE key = 'api_keys' LIMIT 1")
        row = cur.fetchone()
        if row:
            print(row[0])
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
