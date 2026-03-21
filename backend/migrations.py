"""
Database migration script for Corelink B2B Engine.
Run this once when deploying to ensure all columns exist.
"""
from sqlalchemy import text
from database import engine

def run_migrations():
    """Run all database migrations."""
    with engine.connect() as conn:
        # Check if email_sent column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='leads' AND column_name='email_sent'
        """))
        
        if not result.fetchone():
            print("Adding email_sent column...")
            conn.execute(text("ALTER TABLE leads ADD COLUMN email_sent BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ email_sent column added")
        else:
            print("ℹ️ email_sent column already exists")
        
        # Check if email_sent_at column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='leads' AND column_name='email_sent_at'
        """))
        
        if not result.fetchone():
            print("Adding email_sent_at column...")
            conn.execute(text("ALTER TABLE leads ADD COLUMN email_sent_at TIMESTAMP"))
            conn.commit()
            print("✅ email_sent_at column added")
        else:
            print("ℹ️ email_sent_at column already exists")
        
        print("🎉 All migrations complete!")

if __name__ == "__main__":
    run_migrations()
