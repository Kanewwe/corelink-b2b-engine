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
        "users": ["role", "vendor_id"],
        "vendors": ["user_id", "company_name", "pricing_config"],
        "leads": [
            "user_id", 
            "email_sent", 
            "email_sent_at", 
            "contact_name", 
            "contact_role", 
            "contact_email", 
            "contact_confidence",
            "website_url",
            "domain",
            "email_candidates",
            "mx_valid",
            "description",
            "extracted_keywords",
            "assigned_bd",
            "phone",
            "address",
            "city",
            "state",
            "zip_code",
            "categories",
            "source_domain",
            "scrape_location",
            "employee_count",
            "revenue_range"
        ],
        "email_campaigns": ["user_id", "lead_id"],
        "email_templates": ["user_id"],
        "email_logs": ["user_id"]
    }

    print(f"🚀 Starting migration on: {engine.url.render_as_string(hide_password=True)}")
    
    with engine.connect() as conn:
        # Check existing tables
        try:
            if "postgresql" in str(engine.url):
                res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
                tables = [row[0] for row in res.fetchall()]
                print(f"📊 Detected tables: {', '.join(tables)}")
            else:
                res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in res.fetchall()]
                print(f"📊 Detected tables: {', '.join(tables)}")
        except Exception as e:
            print(f"⚠️ Could not list tables: {e}")

        for table, columns in tables_to_patch.items():
            print(f"🔎 Checking table: {table}")
            for column in columns:
                try:
                    # Define type based on column name
                    col_type = "INTEGER"
                    if column == "email_sent": col_type = "BOOLEAN DEFAULT FALSE"
                    if column == "email_sent_at": col_type = "TIMESTAMP"
                    if column == "email_source": col_type = "VARCHAR(50)"
                    if column == "contact_name": col_type = "VARCHAR(255)"
                    if column == "contact_role": col_type = "VARCHAR(255)"
                    if column == "contact_email": col_type = "VARCHAR(255)"
                    if column in ["user_id", "lead_id", "mx_valid", "contact_confidence"]: col_type = "INTEGER"
                    if column in ["email_sent"]: col_type = "BOOLEAN DEFAULT FALSE"
                    if column in ["email_sent_at", "created_at"]: col_type = "TIMESTAMP"
                    if column in ["company_name", "domain", "status", "assigned_bd", "contact_name", "contact_role", "contact_email", "phone", "address", "city", "state", "zip_code", "categories", "source_domain", "scrape_location", "employee_count", "revenue_range", "website_url", "email_candidates", "extracted_keywords", "ai_tag", "description"]: col_type = "TEXT"
                    
                    # More aggressive check
                    has_column = False
                    try:
                        if "postgresql" in str(engine.url):
                            check_sql = text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
                            has_column = conn.execute(check_sql).fetchone() is not None
                        else:
                            res = conn.execute(text(f"PRAGMA table_info({table})"))
                            has_column = column in [row[1] for row in res.fetchall()]
                    except:
                        pass

                    if not has_column:
                        print(f"➕ Adding {column} to {table}...")
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                        conn.commit()
                        print(f"✅ {table}.{column} added successfully")
                    else:
                        print(f"✔️ {table}.{column} already exists")
                        
                except Exception as e:
                    err_msg = str(e).lower()
                    if "already exists" in err_msg or "duplicate" in err_msg:
                        print(f"✔️ {table}.{column} already exists (confirmed by error)")
                        continue
                    print(f"❌ Failed to process {table}.{column}: {e}")
        
    print("🎉 Database migration check complete!")

if __name__ == "__main__":
    run_migrations()
