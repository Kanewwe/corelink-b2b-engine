import sys
import os

# Add the current directory to the path so we can import the models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base
import models
from sqlalchemy import create_engine, text

def run_migration():
    print("🚀 [Migration] Aligning v3.4 SA Standards...")
    
    # 建立所有新表 (TransactionLog)
    Base.metadata.create_all(bind=engine)
    print("✅ [Migration] Table 'transaction_logs' created (or already exists).")
    
    # 擴充 ScrapeLog 欄位 (ScrapeLog)
    with engine.connect() as conn:
        # Check if columns exist
        try:
            conn.execute(text("SELECT response_time FROM scrape_logs LIMIT 1"))
            print("ℹ️ [Migration] 'response_time' already exists in 'scrape_logs'.")
        except Exception:
            print("🏗️ [Migration] Adding 'response_time' and 'http_status' to 'scrape_logs'...")
            conn.execute(text("ALTER TABLE scrape_logs ADD COLUMN response_time DECIMAL(10,3)"))
            conn.execute(text("ALTER TABLE scrape_logs ADD COLUMN http_status INTEGER"))
            conn.commit()
            print("✅ [Migration] 'scrape_logs' columns added.")

    print("🎉 [Migration] v3.4 SA Standards Alignment Complete.")

if __name__ == "__main__":
    run_migration()
