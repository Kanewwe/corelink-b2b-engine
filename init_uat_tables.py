
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from backend.database import Base, DATABASE_URL
import backend.models as models # Ensure models are registered

print(f"Connecting to: {DATABASE_URL}")

def init_uat():
    engine = create_engine(DATABASE_URL, connect_args={"options": "-c search_path=uat"})
    
    with engine.connect() as conn:
        print("Ensuring UAT schema exists...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS uat"))
        conn.commit()
        
        print("Creating tables in UAT schema...")
        Base.metadata.create_all(bind=engine)
        print("Tables created.")

if __name__ == "__main__":
    init_uat()
