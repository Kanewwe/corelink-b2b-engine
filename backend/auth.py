"""
Linkora Authentication Module
包含：Session 管理、密碼 hash、依賴注入
"""

from fastapi import HTTPException, Depends, Request, Cookie
from sqlalchemy.orm import Session
from database import get_db
from models import User, Session as SessionModel, Subscription, Plan, UsageLog
from datetime import datetime, timedelta
from typing import Optional
import uuid

# Session 有效期（天）
SESSION_EXPIRY_DAYS = 30


# ══════════════════════════════════════════
# Session 管理
# ══════════════════════════════════════════

def create_session(db: Session, user: User, ip_address: str = None, user_agent: str = None) -> SessionModel:
    """為用戶建立新 session"""
    session = SessionModel.create_for_user(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(session)
    
    # 更新用戶最後登入時間
    user.last_login_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """取得 session，如果過期或不存在回傳 None"""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id
    ).first()
    
    if session and not session.is_expired():
        # 更新最後活躍時間
        session.last_active_at = datetime.utcnow()
        db.commit()
        return session
    
    return None


def delete_session(db: Session, session_id: str) -> bool:
    """刪除 session"""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id
    ).first()
    
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def delete_all_user_sessions(db: Session, user_id: int) -> int:
    """刪除用戶所有 session（登出所有裝置）"""
    count = db.query(SessionModel).filter(
        SessionModel.user_id == user_id
    ).delete()
    db.commit()
    return count


def cleanup_expired_sessions(db: Session) -> int:
    """清理過期 session"""
    count = db.query(SessionModel).filter(
        SessionModel.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    return count


# ══════════════════════════════════════════
# 用戶取得 helper
# ══════════════════════════════════════════

def get_user_plan(db: Session, user_id: int) -> Plan:
    """取得用戶目前有效方案（沒有就回傳 free plan）"""
    now = datetime.utcnow()
    
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(['active', 'trial']),
        Subscription.current_period_end > now
    ).first()
    
    if subscription and subscription.plan:
        return subscription.plan
    
    # 沒有有效訂閱 → 回傳 free plan
    try:
        free_plan = db.query(Plan).filter(Plan.name == "free").first()
        if free_plan:
            return free_plan
    except Exception as e:
        print(f"⚠️ [auth] Error fetching free plan: {e}")
    
    # Emergency fallback if even 'free' doesn't exist yet (v3.6 stability)
    return Plan(name="free_fallback", display_name="初始化中...", max_customers=50, max_emails_month=10)


def get_user_usage(db: Session, user_id: int, plan: Plan = None) -> UsageLog:
    """取得用戶本月用量"""
    try:
        return UsageLog.get_or_create(db, user_id)
    except Exception as e:
        print(f"⚠️ [auth] Error fetching usage: {e}")
        return None # get_user_full_info will handle the None case


def get_user_full_info(db: Session, user: User) -> dict:
    """取得用戶完整資訊（含方案、用量、訂閱狀態）"""
    plan = get_user_plan(db, user.id)
    usage = get_user_usage(db, user.id)
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(['active', 'trial'])
    ).first()
    
    return {
        "user": user.to_dict(),
        "plan": plan.to_dict() if plan and hasattr(plan, 'to_dict') else None,
        "usage": usage.to_dict(plan) if usage and hasattr(usage, 'to_dict') else {"error": "usage_not_ready"},
        "subscription": subscription.to_dict() if subscription and hasattr(subscription, 'to_dict') else None
    }


# ══════════════════════════════════════════
# 權限檢查函數
# ══════════════════════════════════════════

def require_role(allowed_roles: list):
    """
    工廠函數：檢查用戶角色權限
    用法：@app.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    def checker(
        request: Request,
        session_id: Optional[str] = Cookie(None),
        db: Session = Depends(get_db)
    ):
        # 優先從 Authorization Header 取得 Token (Bearer Token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.split(" ")[1]

        if not session_id:
            raise HTTPException(status_code=401, detail="請先登入")
        
        from models import Session as SessionModel # Lazy import to avoid circular dep if any
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session or session.expires_at < datetime.utcnow() or not session.user:
            raise HTTPException(status_code=401, detail="登入已過期或無效")
            
        if session.user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="權限不足，拒絕訪問")
            
        return session.user
    return checker


def check_feature(feature_name: str):
    """
    工廠函數：生成檢查特定功能的 Dependency
    
    用法：
    @app.get("/some-endpoint")
    async def endpoint(current_user=Depends(check_feature("ai_email"))):
        ...
    """
    def checker(
        session_id: Optional[str] = Cookie(None),
        request: Request = None,
        db: Session = Depends(get_db)
    ):
        if not session_id:
            raise HTTPException(status_code=401, detail="請先登入")
        
        session = get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session 已過期，請重新登入")
        
        user = session.user
        plan = get_user_plan(db, user.id)
        
        # 檢查功能是否啟用
        feature_attr = f"feature_{feature_name}"
        if not getattr(plan, feature_attr, False):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "feature_not_available",
                    "message": f"此功能需要升級至專業方案。目前方案：{plan.display_name}",
                    "current_plan": plan.name,
                    "required_plan": "pro"
                }
            )
        
        return user
    
    return checker


def check_usage_limit(limit_type: str):
    """
    工廠函數：生成檢查用量限制的 Dependency
    
    用法：
    @app.post("/send-email")
    async def send_email(current_user=Depends(check_usage_limit("email"))):
        ...
    """
    def checker(
        session_id: Optional[str] = Cookie(None),
        db: Session = Depends(get_db)
    ):
        if not session_id:
            raise HTTPException(status_code=401, detail="請先登入")
        
        session = get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session 已過期，請重新登入")
        
        user = session.user
        plan = get_user_plan(db, user.id)
        usage = get_user_usage(db, user.id)
        
        # 限制欄位對照
        limit_map = {
            "email": ("emails_sent_count", "max_emails_month", "emails_month"),
            "customer": ("customers_count", "max_customers", "customers"),
            "autominer": ("autominer_runs_count", "max_autominer_runs", "autominer_runs"),
            "template": ("templates_count", "max_templates", "templates"),
        }
        
        if limit_type not in limit_map:
            return user
        
        used_field, limit_field, display_name = limit_map[limit_type]
        used = getattr(usage, used_field, 0)
        limit = getattr(plan, limit_field, 0)
        
        # -1 表示無限制
        if limit != -1 and used >= limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "usage_limit_exceeded",
                    "message": f"本月 {display_name} 用量已達上限（{used}/{limit}）",
                    "type": limit_type,
                    "used": used,
                    "limit": limit,
                    "upgrade_required": True,
                    "current_plan": plan.name
                }
            )
        
        return user
    
    return checker


# ══════════════════════════════════════════
# FastAPI Dependencies（可直接用在路由）
# ══════════════════════════════════════════

async def get_current_user(
    request: Request,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """取得當前登入用戶 (支援 Cookie 與 Authorization Header)"""
    # 支援 Bearer Token 
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.split(" ")[1]

    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期，請重新登入")
    
    return session.user


async def get_current_user_optional(
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """取得當前用戶（可選，沒登入也不會錯誤）"""
    if not session_id:
        return None
    
    session = get_session(db, session_id)
    if not session:
        return None
    
    return session.user


# ══════════════════════════════════════════
# 用量更新 helper
# ══════════════════════════════════════════

def increment_usage(db: Session, user_id: int, field: str, amount: int = 1):
    """增加用戶用量"""
    usage = UsageLog.get_or_create(db, user_id)
    
    if hasattr(usage, field):
        setattr(usage, field, getattr(usage, field, 0) + amount)
    
    db.commit()


def decrement_usage(db: Session, user_id: int, field: str, amount: int = 1):
    """減少用戶用量"""
    usage = UsageLog.get_or_create(db, user_id)
    
    if hasattr(usage, field):
        current = getattr(usage, field, 0)
        setattr(usage, field, max(0, current - amount))
    
    db.commit()


def set_usage(db: Session, user_id: int, field: str, value: int):
    """設定用戶用量（直接覆寫）"""
    usage = UsageLog.get_or_create(db, user_id)
    
    if hasattr(usage, field):
        setattr(usage, field, value)
    
    db.commit()


def sync_customers_count(db: Session, user_id: int):
    """同步客戶數量（從 leads 表統計）"""
    from models import Lead
    
    count = db.query(Lead).filter(Lead.user_id == user_id).count()
    set_usage(db, user_id, "customers_count", count)


def sync_templates_count(db: Session, user_id: int):
    """同步模板數量（從 templates 表統計）"""
    from models import EmailTemplate
    
    count = db.query(EmailTemplate).filter(EmailTemplate.user_id == user_id).count()
    set_usage(db, user_id, "templates_count", count)


def check_user_quota(db: Session, user_id: int, quota_type: str = "customers") -> dict:
    """
    v2.7.3: 檢查用戶配額
    回傳: {"allowed": bool, "remaining": int, "message": str}
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"allowed": False, "remaining": 0, "message": "用戶不存在"}
    
    # Vendor 無限制
    if user.role == "vendor":
        return {"allowed": True, "remaining": -1, "message": "無限制"}
    
    # Admin 也無限制
    if user.role == "admin":
        return {"allowed": True, "remaining": -1, "message": "無限制"}
    
    # Member 需檢查配額
    plan = get_user_plan(db, user_id)
    usage = get_user_usage(db, user_id)
    
    quota_map = {
        "customers": ("customers_count", "max_customers"),
        "emails": ("emails_sent_count", "max_emails_month"),
        "templates": ("templates_count", "max_templates"),
        "autominer": ("autominer_runs_count", "max_autominer_runs")
    }
    
    if quota_type not in quota_map:
        return {"allowed": True, "remaining": -1, "message": "未知類型，預設允許"}
    
    used_field, limit_field = quota_map[quota_type]
    used = getattr(usage, used_field, 0)
    limit = getattr(plan, limit_field, 0)
    
    # -1 表示無限制
    if limit == -1:
        return {"allowed": True, "remaining": -1, "message": "無限制"}
    
    remaining = max(0, limit - used)
    
    if used >= limit:
        plan_name = plan.display_name if plan else "未知方案"
        return {
            "allowed": False, 
            "remaining": 0, 
            "message": f"本月 {quota_type} 配額已用完（{used}/{limit}），請升級方案。目前方案：{plan_name}"
        }
    
    return {"allowed": True, "remaining": remaining, "message": f"剩餘 {remaining} 筆配額"}
