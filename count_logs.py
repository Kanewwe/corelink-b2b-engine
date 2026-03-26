
import psycopg2

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def run():
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM uat.scrape_logs")
    print(f"Total Logs in UAT: {cur.fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    run()
