"""
Database migration script for Corelink B2B Engine.
Run this once when deploying to ensure all columns exist.
"""
from sqlalchemy import text
from database import engine

def run_migrations():
    """Run all database migrations."""
    import sqlalchemy
    import os
    
    # v3.7.26: 支援 UAT schema
    schema_name = os.getenv("APP_ENV", "public")
    if schema_name == "uat":
        schema_name = "uat"
    else:
        schema_name = "public"
    
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
            # v3.7.29 行業標籤欄位
            "industry_code",
            "industry_name",
            "sub_industry_code",
            "sub_industry_name",
            "industry_tags",
            "email_verified",
            "email_confidence",
        ],
        "scrape_tasks": ["miner_mode"],
        "system_settings": ["user_id", "key", "value"],
        "global_leads": [
            # v3.7.29 行業標籤欄位
            "industry_code",
            "industry_name",
            "sub_industry_code",
            "sub_industry_name",
            "industry_tags",
            "employee_count",
            "employee_range",
            "email_verified",
            "email_confidence",
            "email_source",
            "source_mode",
            "sync_count",
            "last_synced_at",
        ]
    }

    print(f"🚀 Starting migration on: {engine.url.render_as_string(hide_password=True)}")
    print(f"📦 Schema: {schema_name}")
    
    with engine.connect() as conn:
        # 設定 search_path
        conn.execute(text(f"SET search_path TO {schema_name}"))
        
        # 1. Ensure global_leads table exists (The Isolation Pool)
        create_global_table = f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.global_leads (
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
            print(f"✅ {schema_name}.global_leads table ensured")
        except Exception as e:
            print(f"⚠️ Error ensuring global_leads: {e}")

        # 2. Patch existing tables
        for table, columns in tables_to_patch.items():
            print(f"🔎 Checking table: {schema_name}.{table}")
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
                    
                    # Check if column exists
                    has_column = False
                    try:
                        check_sql = text(f"SELECT 1 FROM information_schema.columns WHERE table_schema='{schema_name}' AND table_name='{table}' AND column_name='{column}'")
                        has_column = conn.execute(check_sql).fetchone() is not None
                    except:
                        pass

                    if not has_column:
                        print(f"➕ Adding {column} to {schema_name}.{table}...")
                        conn.execute(text(f"ALTER TABLE {schema_name}.{table} ADD COLUMN {column} {col_type}"))
                        conn.commit()
                        print(f"✅ {schema_name}.{table}.{column} added successfully")
                    else:
                        print(f"✔️ {schema_name}.{table}.{column} already exists")
                        
                except Exception as e:
                    err_msg = str(e).lower()
                    if "already exists" in err_msg or "duplicate" in err_msg:
                        print(f"✔️ {schema_name}.{table}.{column} already exists (confirmed by error)")
                        continue
                    print(f"❌ Failed to process {schema_name}.{table}.{column}: {e}")
        
    print("🎉 Database migration check complete!")

if __name__ == "__main__":
    run_migrations()
