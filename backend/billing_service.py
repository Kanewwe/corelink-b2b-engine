"""
Linkora v3.5 - Granular Billing Engine (SA Spec)
- Usage Weights:
  - Scrape Success: 10 pts
  - AI Intelligence: 5 pts
  - Email Sent: 1 pt
"""

from database import SessionLocal
from database import SessionLocal
from datetime import datetime
import json

# SA Spec Weights
WEIGHTS = {
    "scrape": 10,
    "ai_intelligence": 5,
    "email_sent": 1
}

def deduct_points(user_id: int, action_type: str, meta: dict = None) -> bool:
    """
    SA v3.5: 扣除點數並記錄流水
    Returns: True if successful, False if insufficient points
    """
    if action_type not in WEIGHTS:
        print(f"⚠️ [Billing] Unknown action type: {action_type}")
        return False
    
    points_to_deduct = WEIGHTS[action_type]
    db = SessionLocal()
    
    try:
        # 1. 檢查目前點數 (這裡假設 points 存於 User 或 Subscription，
        # 在目前的 models.py 中，我們需要新增一個 points 欄位於 User 或使用 TransactionLog 加總)
        # 為了簡化初期實作，我們從 TransactionLog 計算餘額
        
        from sqlalchemy import func
        import models # Lazy loading to break circular import v3.5
        balance = db.query(func.sum(models.TransactionLog.point_delta)).filter(
            models.TransactionLog.user_id == user_id
        ).scalar() or 1000  # 預設贈送 1000 點給現有用戶 (v3.5 Migration)
        
        if balance < points_to_deduct:
            print(f"❌ [Billing] User {user_id} 點數不足 (剩餘 {balance}, 需 {points_to_deduct})")
            return False
        
        # 2. 記錄扣點交易
        import models
        new_tx = models.TransactionLog(
            user_id=user_id,
            action_type=action_type,
            point_delta=-points_to_deduct,
            description=json.dumps(meta) if meta else None
        )
        db.add(new_tx)
        
        # 3. 同步更新 UsageLog (v3.0 Legacy Support)
        import models
        usage = models.UsageLog.get_or_create(db, user_id)
        if action_type == "scrape":
            usage.customers_count += 1
        elif action_type == "email_sent":
            usage.emails_sent_count += 1
        # ai_intelligence doesn't have a specific field in usage_logs currently, 
        # but TransactionLog is the primary source in v3.5
        
        db.commit()
        print(f"💰 [Billing] User {user_id} -{points_to_deduct} pts ({action_type})")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"⚠️ [Billing Error] {e}")
        return False
    finally:
        db.close()

def get_point_balance(user_id: int) -> int:
    """計算用戶剩餘點數"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        import models # Lazy loading to break circular import v3.5
        balance = db.query(func.sum(models.TransactionLog.point_delta)).filter(
            models.TransactionLog.user_id == user_id
        ).scalar() or 1000 # Default for existing users
    except Exception as e:
        print(f"⚠️ [Billing] Balance check fallback: {e}")
        return 1000  # Fallback during initial migration (v3.5)
    finally:
        db.close()
    return int(balance)
