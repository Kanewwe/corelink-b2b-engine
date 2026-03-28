import pytest
import models
from auth import get_user_plan, get_user_usage, check_user_quota, increment_usage

def test_free_plan_limits(db_session):
    """
    驗證 Free 方案的用量限制。
    預設 Free 方案 max_customers=50。
    """
    # 1. 建立 Free 方案用戶
    user = models.User(email="free_user@test.com", name="Free User")
    db_session.add(user)
    db_session.commit()
    
    # 2. 為用戶建立 Free 訂閱 (conftest 已建立 free plan)
    free_plan = db_session.query(models.Plan).filter(models.Plan.name == "free").first()
    sub = models.Subscription(
        user_id=user.id, 
        plan_id=free_plan.id, 
        status="active",
        current_period_end=models.datetime.utcnow() + models.timedelta(days=30)
    )
    db_session.add(sub)
    db_session.commit()
    
    # 3. 檢查初始配額
    quota = check_user_quota(db_session, user.id, "customers")
    assert quota["allowed"] is True
    assert quota["remaining"] == 50
    
    # 4. 模擬用量達到上限
    usage = get_user_usage(db_session, user.id)
    usage.customers_count = 50
    db_session.commit()
    
    # 5. 驗證配額攔截
    quota_after = check_user_quota(db_session, user.id, "customers")
    assert quota_after["allowed"] is False
    assert "配額已用完" in quota_after["message"]

def test_pro_plan_extended_limits(db_session):
    """
    驗證 Pro 方案具有更高的限制。
    預設 Pro 方案 max_customers=500。
    """
    user = models.User(email="pro_user@test.com", name="Pro User")
    db_session.add(user)
    db_session.commit()
    
    pro_plan = db_session.query(models.Plan).filter(models.Plan.name == "pro").first()
    sub = models.Subscription(
        user_id=user.id, 
        plan_id=pro_plan.id, 
        status="active",
        current_period_end=models.datetime.utcnow() + models.timedelta(days=30)
    )
    db_session.add(sub)
    db_session.commit()
    
    # 模擬用量 50 (Free 版的上限)
    increment_usage(db_session, user.id, "customers_count", 50)
    
    # Pro 版應仍允許
    quota = check_user_quota(db_session, user.id, "customers")
    assert quota["allowed"] is True
    assert quota["remaining"] == 450

def test_vendor_unlimited_access(db_session):
    """
    驗證 Vendor 角色無限制。
    """
    vendor = models.User(email="vendor_api@test.com", name="Vendor", role="vendor")
    db_session.add(vendor)
    db_session.commit()
    
    # 即使沒有訂閱，Vendor 也應被視為無限制
    quota = check_user_quota(db_session, vendor.id, "customers")
    assert quota["allowed"] is True
    assert quota["remaining"] == -1
    assert "無限制" in quota["message"]
