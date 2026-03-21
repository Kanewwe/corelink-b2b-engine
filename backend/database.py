from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# DATABASE_URL from env (Render auto-injects for managed PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./corelink.db")

# Fix Render's postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False, PostgreSQL doesn't
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

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
    """Import all models and create tables."""
    import models  # noqa - ensures models are registered
    Base.metadata.create_all(bind=engine)
