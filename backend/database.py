from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# ─── DATABASE_URL from env (Enforced: PostgreSQL) ───
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("❌ [CRITICAL] DATABASE_URL is not set! SQLite is deprecated. Please configure PostgreSQL.")

APP_ENV = os.getenv("APP_ENV", "production")  # 'production' or 'uat'

# Fix Render's postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ─── PostgreSQL Connection Arguments ───
connect_args = {}

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
            if schema_name != "public":
                print(f"🛠️ [Database] Ensuring schema '{schema_name}' exists...")
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
                
    Base.metadata.create_all(bind=engine)
    
    # v3.2: Migration: 為已存在的資料表新增新欄位
    _run_migrations(engine)


def _run_migrations(engine):
    """v3.2: 為已存在的資料表新增 v3.2 新增的欄位"""
    from sqlalchemy import text
    
    migrations = [
        # leads 表新增 AI 評分欄位
        ("leads", "ai_score", "INTEGER DEFAULT 0"),
        ("leads", "ai_score_tags", "TEXT"),
        ("leads", "ai_brief", "TEXT"),
        ("leads", "ai_suggestions", "TEXT"),
        ("leads", "ai_scored_at", "TIMESTAMP"),
        # leads 表新增 error_message (爬蟲錯誤)
        ("leads", "error_message", "TEXT"),
    ]
    
    with engine.connect() as conn:
        for table, column, column_type in migrations:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {column_type}"
                ))
                conn.commit()
            except Exception as e:
                # 忽略已經存在的欄位錯誤
                if "already exists" not in str(e).lower():
                    print(f"⚠️ Migration warning: {table}.{column}: {e}")
        # 确保 commit
        try:
            conn.commit()
        except:
            pass
