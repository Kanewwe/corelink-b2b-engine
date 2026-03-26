
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateTable
from backend.database import Base, DATABASE_URL
import backend.models as models

def create_manual():
    # Use PUBLIC engine to get the DDL but apply it to UAT
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Ensuring UAT schema exists...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS uat"))
        conn.commit()
        
        # Invert the search path to UAT
        conn.execute(text("SET search_path TO uat, public"))
        
        print("Creating all tables in UAT schema...")
        for table in Base.metadata.sorted_tables:
            # Drop if exists for clean start (BE CAREFUL IN PROD, but this is UAT setup)
            # conn.execute(text(f"DROP TABLE IF EXISTS uat.{table.name} CASCADE"))
            
            ddl = str(CreateTable(table).compile(engine))
            # Inject 'uat.' before table name
            # We use a safer replacement: FIND 'CREATE TABLE table_name'
            target = f"CREATE TABLE {table.name}"
            if target in ddl:
                ddl = ddl.replace(target, f"CREATE TABLE uat.{table.name}")
            
            # Handle constraints/indexes
            # Actually, the simplest is to just run the DDL with search_path=uat
            # Let's try ONE MORE TIME with search_path but no manual injection
            try:
                print(f"Executing DDL for {table.name}...")
                conn.execute(text(ddl))
                conn.commit()
            except Exception as e:
                print(f"Error on {table.name}: {e}")
                conn.rollback()

if __name__ == "__main__":
    create_manual()
