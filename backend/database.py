from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# DATABASE_URL from env (Render auto-injects for managed PostgreSQL)
# Supports separate schemas for PRD/UAT on a single instance
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./corelink.db")
APP_ENV = os.getenv("APP_ENV", "production")  # 'production' or 'uat'

# Fix Render's postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# PostgreSQL Connection Arguments
connect_args = {}

if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False
else:
    # PostgreSQL specific configs
    # 1. SSL is required for Render PG
    # 2. Schema switching via search_path
    schema_name = "public" if APP_ENV == "production" else "uat"
    connect_args["options"] = f"-c search_path={schema_name}"
    
    # Ensure SSL is active for remote connections
    if "render.com" in DATABASE_URL:
        # Some drivers might need sslmode in the URL, but options handle it for SQLAlchemy usually
        # To be safe, ensure the URL has sslmode=require if not present
        if "sslmode" not in DATABASE_URL:
            separator = "&" if "?" in DATABASE_URL else "?"
            DATABASE_URL += f"{separator}sslmode=require"

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Import all models and create tables. Also creates schemas for PostgreSQL."""
    import models  # noqa - ensures models are registered
    
    # 針對 PostgreSQL 預先建立 Schema
    if "postgresql" in DATABASE_URL:
        from sqlalchemy import text
        with engine.connect() as conn:
            schema_name = "uat" if APP_ENV == "uat" else "public"
            from logger import add_log
            add_log(f"DEBUG: database.py init_db using schema_name={schema_name}, env={os.getenv('APP_ENV')}")
            if schema_name != "public":
                print(f"🛠️ [Database] Ensuring schema '{schema_name}' exists...")
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
                
    Base.metadata.create_all(bind=engine)
