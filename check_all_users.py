
import psycopg2

conn_str = "postgresql://corelink_db_cb70_user:F4IrAzrlYNchYvlU0BQmlgLWL4o9laHc@dpg-d6v4ghmuk2gs738i8ovg-a.oregon-postgres.render.com:5432/corelink_db_cb70"

def check_all():
    try:
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        
        for schema in ['public', 'uat']:
            print(f"\n--- Checking Schema: {schema} ---")
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = 'users'")
            cols = [r[0] for r in cur.fetchall()]
            print(f"Columns: {cols}")
            
            if 'company_name' not in cols:
                print(f"Adding company_name to {schema}.users...")
                cur.execute(f"ALTER TABLE {schema}.users ADD COLUMN company_name VARCHAR(200)")
                conn.commit()
                print("Added.")
            else:
                print(f"company_name already exists in {schema}.users.")
            
            # Check others
            for col in ['last_login_at', 'updated_at', 'role', 'is_active', 'is_verified']:
                if col not in cols:
                    print(f"Adding {col} to {schema}.users...")
                    cur.execute(f"ALTER TABLE {schema}.users ADD COLUMN {col} VARCHAR(200)") # Roughly
                    conn.commit()

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all()
