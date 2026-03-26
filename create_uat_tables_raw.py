
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateTable
from backend.database import Base, DATABASE_URL
import backend.models as models

def create_raw():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Ensuring UAT schema exists...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS uat"))
        conn.commit()
        
        # We'll run each DDL manually
        print("Creating tables in UAT schema via raw SQL...")
        for table in Base.metadata.sorted_tables:
            print(f"Creating table: uat.{table.name}")
            # Generate the DDL and modify it to include the schema name
            ddl = str(CreateTable(table).compile(engine))
            # Rough hack to inject schema: replace 'CREATE TABLE table_name' with 'CREATE TABLE uat.table_name'
            # Note: This is brittle but effective for a quick fix if the table doesn't have a schema set.
            if f"CREATE TABLE {table.name}" in ddl:
                ddl = ddl.replace(f"CREATE TABLE {table.name}", f"CREATE TABLE uat.{table.name}")
            
            # Also handle foreign keys within the same schema
            # Actually, the simplest way is to SET search_path before running the DDL
            try:
                conn.execute(text("SET search_path TO uat"))
                conn.execute(text(str(CreateTable(table).compile(engine))))
                conn.commit()
            except Exception as e:
                print(f"Error creating {table.name}: {e}")
                conn.rollback()
        
        print("Done.")

if __name__ == "__main__":
    create_raw()
