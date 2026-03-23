"""
Database migration script for Corelink B2B Engine.
Run this once when deploying to ensure all columns exist.
"""
from sqlalchemy import text
from database import engine

def run_migrations():
    """Run all database migrations."""
    import sqlalchemy
    
    tables_to_patch = {
        "leads": ["user_id", "email_sent", "email_sent_at"],
        "email_campaigns": ["user_id"],
        "email_templates": ["user_id"],
        "email_logs": ["user_id"]
    }

    with engine.connect() as conn:
        for table, columns in tables_to_patch.items():
            for column in columns:
                try:
                    # Check if column exists (Different for SQLite vs Postgres)
                    if "sqlite" in str(engine.url):
                        res = conn.execute(text(f"PRAGMA table_info({table})"))
                        existing_cols = [row[1] for row in res.fetchall()]
                        if column in existing_cols:
                            continue
                    else:
                        # Postgres
                        res = conn.execute(text(f"""
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='{table}' AND column_name='{column}'
                        """))
                        if res.fetchone():
                            continue

                    print(f"Adding column {column} to table {table}...")
                    
                    # Define type based on column name
                    col_type = "INTEGER"
                    if column == "email_sent": col_type = "BOOLEAN DEFAULT 0"
                    if column == "email_sent_at": col_type = "TIMESTAMP"
                    if column == "user_id": col_type = "INTEGER"
                    
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    conn.commit()
                    print(f"✅ {table}.{column} added")
                except Exception as e:
                    print(f"⚠️ Could not add {column} to {table}: {e}")
        
        print("🎉 Database migrations complete!")

if __name__ == "__main__":
    run_migrations()
