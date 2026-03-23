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
                    # Define type based on column name
                    col_type = "INTEGER"
                    if column == "email_sent": col_type = "BOOLEAN DEFAULT FALSE"
                    if column == "email_sent_at": col_type = "TIMESTAMP"
                    
                    print(f"Trying to add {column} to {table}...")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    conn.commit()
                    print(f"✅ {table}.{column} added")
                except Exception as e:
                    # Ignore "already exists" errors (standard Postgres and SQLite error messages)
                    err_msg = str(e).lower()
                    if "already exists" in err_msg or "duplicate column" in err_msg or "has no column" in err_msg:
                        # For SQLite, it might say "duplicate column name"
                        continue
                    print(f"ℹ️ {table}.{column} could not be added (likely already exists): {e}")
        
        print("🎉 Database migrations complete!")

if __name__ == "__main__":
    run_migrations()
