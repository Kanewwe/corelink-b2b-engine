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
        "users": ["role", "reset_token", "reset_expires", "verify_token"],
        "leads": [
            "user_id", 
            "global_id",
            "email_sent", 
            "email_sent_at", 
            "contact_email", 
            "website_url",
            "domain",
            "email_candidates",
            "ai_tag",
            "description",
            "extracted_keywords",
            "scrape_location",
            # v3.7 新增欄位
            "override_name",
            "override_email",
            "personal_notes",
            "custom_tags",
            # v3.2 AI 欄位
            "ai_score",
            "ai_score_tags",
            "ai_brief",
            "ai_suggestions",
            "ai_scored_at",
        ],
        "scrape_tasks": ["miner_mode"],
        "system_settings": ["user_id", "key", "value"]
    }

    print(f"🚀 Starting migration on: {engine.url.render_as_string(hide_password=True)}")
    
    with engine.connect() as conn:
        # 1. Ensure global_leads table exists (The Isolation Pool)
        create_global_table = """
            CREATE TABLE IF NOT EXISTS global_leads (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(200),
                domain VARCHAR(100) UNIQUE,
                website_url VARCHAR(500),
                description TEXT,
                contact_email VARCHAR(255),
                email_candidates TEXT,
                phone VARCHAR(50),
                address TEXT,
                ai_tag VARCHAR(100),
                industry VARCHAR(100),
                source VARCHAR(100),
                last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        try:
            conn.execute(text(create_global_table))
            conn.commit()
            print("✅ global_leads table ensured (PostgreSQL)")
        except Exception as e:
            print(f"⚠️ Error ensuring global_leads: {e}")

        # 2. Patch existing tables
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
                    # v3.7 新增欄位類型
                    if column in ["override_name"]: col_type = "VARCHAR(200)"
                    if column in ["override_email"]: col_type = "VARCHAR(255)"
                    if column in ["personal_notes"]: col_type = "TEXT"
                    if column in ["custom_tags"]: col_type = "VARCHAR(255)"
                    # v3.2 AI 欄位類型
                    if column == "ai_score": col_type = "INTEGER DEFAULT 0"
                    if column in ["ai_score_tags", "ai_brief", "ai_suggestions"]: col_type = "TEXT"
                    if column == "ai_scored_at": col_type = "TIMESTAMP"
                    
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
