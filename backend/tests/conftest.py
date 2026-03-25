import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os

# Add backend to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
import models

# Use SQLite in-memory for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    
    # Setup initial data (Plans)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    free_plan = models.Plan(name="free", display_name="Free Plan", max_customers=50)
    pro_plan = models.Plan(name="pro", display_name="Pro Plan", max_customers=500)
    db.add(free_plan)
    db.add(pro_plan)
    db.commit()
    db.close()
    
    return engine

@pytest.fixture
def db_session(engine):
    """Provides a transactional database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_user(db_session):
    """Creates a mock user for testing."""
    user = models.User(
        email="test@example.com",
        name="Test User",
        role="member"
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user
