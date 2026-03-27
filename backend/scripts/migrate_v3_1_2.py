import sys
import os

# Add parent directory to path to import database and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine, APP_ENV

def migrate():
    schema_name = "uat" if APP_ENV == "uat" else "public"
    print(f"🚀 [Migration] Starting schema check for '{schema_name}'...")
    
    inspector = inspect(engine)
    
    # helper to check if column exists
    def column_exists(table_name, column_name):
        columns = inspector.get_columns(table_name, schema=schema_name)
        return any(c['name'] == column_name for c in columns)

    with engine.connect() as conn:
        # Tables to check
        updates = {
            "leads": [
                ("user_id", "INTEGER"),
                ("override_name", "VARCHAR(200)"),
                ("override_email", "VARCHAR(255)"),
                ("personal_notes", "TEXT"),
                ("custom_tags", "VARCHAR(255)"),
                ("email_source", "VARCHAR"),
                ("industry_taxonomy", "VARCHAR(255)"),
                ("global_id", "INTEGER")
            ],
            "global_leads": [
                ("industry_taxonomy", "VARCHAR(255)"),
                ("is_verified", "BOOLEAN DEFAULT FALSE"),
                ("confidence_score", "INTEGER DEFAULT 0")
            ],
            "global_proposals": [
                ("current_value", "TEXT"),
                ("reason", "VARCHAR(255)")
            ]
        }

        for table, cols in updates.items():
            # Ensure table exists first (Base.metadata.create_all should have handled this, but just in case)
            if not inspector.has_table(table, schema=schema_name):
                print(f"⚠️ [Migration] Table '{table}' not found in schema '{schema_name}'. Skipping column updates.")
                continue

            for col_name, col_type in cols:
                if not column_exists(table, col_name):
                    print(f"➕ [Migration] Adding column '{col_name}' to table '{table}'...")
                    try:
                        conn.execute(text(f"ALTER TABLE {schema_name}.{table} ADD COLUMN {col_name} {col_type}"))
                        print(f"✅ [Migration] Column '{col_name}' added.")
                    except Exception as e:
                        print(f"❌ [Migration] Failed to add column '{col_name}': {e}")
                else:
                    print(f"⭐ [Migration] Column '{col_name}' already exists in '{table}'.")
        
        conn.commit()
    print("🏁 [Migration] Schema update complete.")

if __name__ == "__main__":
    migrate()
