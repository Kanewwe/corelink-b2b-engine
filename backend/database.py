from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# ─── DATABASE_URL from env (Enforced: PostgreSQL for non-test env) ───
DATABASE_URL = os.getenv("DATABASE_URL")
APP_ENV = os.getenv("APP_ENV", "production")  # 'production', 'uat', or 'test'

if not DATABASE_URL and APP_ENV != "test":
    raise EnvironmentError("❌ [CRITICAL] DATABASE_URL is not set! SQLite is deprecated. Please configure PostgreSQL.")

if not DATABASE_URL and APP_ENV == "test":
    DATABASE_URL = "sqlite:///:memory:"
    print("ℹ️ [Database] APP_ENV=test and no DATABASE_URL found. Using SQLite In-Memory.")

# Fix Render's postgres:// -> postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ─── PostgreSQL Connection Arguments ───
connect_args = {}

# 1. SSL is required for Render PG
# 2. Schema switching via search_path (Disabled for v3.5 Global Stability)
# schema_name = "uat" if APP_ENV == "uat" else "public"
# connect_args["options"] = f"-c search_path={schema_name}"
# v3.5: 強制在 connect_args 映射中明確指定 (針對多執行緒池優化)
# if DATABASE_URL and "postgresql" in DATABASE_URL:
#     connect_args["options"] = f"-c search_path={schema_name}"

# Ensure SSL is active for remote connections
if DATABASE_URL and "render.com" in DATABASE_URL:
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
    """v3.2-v3.7: 為已存在的資料表新增欄位"""
    from sqlalchemy import text
    
    schema_name = "uat" if APP_ENV == "uat" else "public"
    
    migrations = [
        # leads 表新增 AI 評分欄位 (v3.2)
        ("leads", "ai_score", "INTEGER DEFAULT 0"),
        ("leads", "ai_score_tags", "TEXT"),
        ("leads", "ai_brief", "TEXT"),
        ("leads", "ai_suggestions", "TEXT"),
        ("leads", "ai_scored_at", "TIMESTAMP"),
        ("leads", "error_message", "TEXT"),
        # leads 表新增 v3.7 欄位
        ("leads", "override_name", "VARCHAR(200)"),
        ("leads", "override_email", "VARCHAR(255)"),
        ("leads", "personal_notes", "TEXT"),
        ("leads", "custom_tags", "VARCHAR(255)"),
        # email_logs 表新增 AI 回信分析欄位 (Sprint 2)
        ("email_logs", "reply_intent", "VARCHAR(50)"),
        ("email_logs", "reply_analysis", "TEXT"),
        ("email_logs", "reply_next_action", "TEXT"),
    ]
    
    with engine.connect() as conn:
        # 確保 search_path 正確
        conn.execute(text(f"SET search_path TO {schema_name}"))
        
        for table, column, column_type in migrations:
            try:
                conn.execute(text(
                    f"ALTER TABLE {schema_name}.{table} ADD COLUMN IF NOT EXISTS {column} {column_type}"
                ))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️ Migration: {table}.{column}: {e}")
