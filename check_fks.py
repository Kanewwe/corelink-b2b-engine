
import psycopg2

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def run():
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    # Check foreign keys for uat.scrape_logs
    cur.execute("""
        SELECT
            tc.constraint_name, 
            kcu.column_name, 
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='scrape_logs' AND tc.table_schema='uat';
    """)
    rows = cur.fetchall()
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    run()
