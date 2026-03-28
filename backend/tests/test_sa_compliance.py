import pytest
import sys
import os

# Align Python path to backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal as TestSessionLocal, engine
import models
from billing_service import deduct_points, get_point_balance
from scraper_utils import log_scrape_health
import json
import uuid

# --- Setup Test Database (Ensuring Tables Exist on the Shared Engine) ---
# Create tables in test DB (Fresh for each run)
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

# --- SA Specification Validation Tests ---

def test_sa_billing_weights():
    """
    SA v3.5 Spec:
    - Scrape: 10 pts
    - AI: 5 pts
    - Email: 1 pt
    """
    db = TestSessionLocal()
    # Create a test user
    test_user = models.User(email=f"test_{uuid.uuid4()}@linkora.com", password_hash="hash", role="member")
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Initialize with 100 points
    initial_tx = models.TransactionLog(user_id=test_user.id, action_type="reload", point_delta=100)
    db.add(initial_tx)
    db.commit()
    
    try:
        # 1. Scrape (10 pts)
        assert deduct_points(test_user.id, "scrape") is True
        assert get_point_balance(test_user.id) == 90
        
        # 2. AI Intelligence (5 pts)
        assert deduct_points(test_user.id, "ai_intelligence") is True
        assert get_point_balance(test_user.id) == 85
        
        # 3. Email (1 pt)
        assert deduct_points(test_user.id, "email_sent") is True
        assert get_point_balance(test_user.id) == 84
        
        # 4. Insufficient Points
        # Empty the points
        drain_tx = models.TransactionLog(user_id=test_user.id, action_type="manual", point_delta=-80)
        db.add(drain_tx)
        db.commit()
        
        # Remaining: 4. Scrape needs 10.
        assert deduct_points(test_user.id, "scrape") is False
        assert get_point_balance(test_user.id) == 4
        
    finally:
        # Cleanup
        db.query(models.TransactionLog).filter(models.TransactionLog.user_id == test_user.id).delete()
        db.delete(test_user)
        db.commit()
        db.close()

def test_sa_scraper_health_logging():
    """
    SA v3.4 Spec:
    - Response time (Seconds)
    - HTTP Status
    """
    db = TestSessionLocal()
    try:
        # Create a dummy task
        task = models.ScrapeTask(user_id=1, market="US", keywords="test", status="Running")
        db.add(task)
        db.commit()
        
        # Log health
        log_scrape_health(
            task_id=task.id,
            message="Health Test",
            level="success",
            response_time=1.234,
            http_status=200,
            keyword="test_kw"
        )
        
        # Verify
        log_entry = db.query(models.ScrapeLog).filter(models.ScrapeLog.task_id == task.id).first()
        assert log_entry is not None
        assert float(log_entry.response_time) == 1.234
        assert log_entry.http_status == 200
        
    finally:
        db.query(models.ScrapeLog).filter(models.ScrapeLog.task_id == task.id).delete()
        db.delete(task)
        db.commit()
        db.close()

if __name__ == "__main__":
    # Manual run support
    print("Running SA Logic Verification...")
    test_sa_billing_weights()
    print("✅ Billing Weights OK")
    test_sa_scraper_health_logging()
    print("✅ Scraper Health OK")
