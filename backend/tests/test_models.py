import pytest
from models import UsageLog, User, Plan
from datetime import datetime

def test_usage_log_get_or_create(db_session, mock_user):
    """Test that UsageLog.get_or_create works correctly."""
    # 1. Create a logs for the first time
    log1 = UsageLog.get_or_create(db_session, mock_user.id)
    assert log1 is not None
    assert log1.user_id == mock_user.id
    assert log1.period_year == datetime.utcnow().year
    assert log1.period_month == datetime.utcnow().month
    
    # 2. Call again, should return the same log
    log2 = UsageLog.get_or_create(db_session, mock_user.id)
    assert log2.id == log1.id
    
    # 3. Verify defaults
    assert log1.customers_count == 0
    assert log1.emails_sent_count == 0

def test_usage_log_to_dict(db_session, mock_user):
    """Test the to_dict method of UsageLog."""
    log = UsageLog.get_or_create(db_session, mock_user.id)
    log.customers_count = 10
    db_session.commit()
    
    plan = db_session.query(Plan).filter(Plan.name == "free").first()
    data = log.to_dict(plan)
    
    assert data["customers"]["used"] == 10
    assert data["customers"]["limit"] == 50
    assert "emails_month" in data
