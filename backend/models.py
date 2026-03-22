"""
Linkora Subscription System - Database Models
包含：users, sessions, subscriptions, plans, usage_logs
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timedelta
import uuid
import bcrypt

# ══════════════════════════════════════════
# Plans（方案定義）
# ══════════════════════════════════════════

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # 'free', 'pro', 'enterprise'
    display_name = Column(String(100))
    price_monthly = Column(DECIMAL(10,2), default=0)
    price_yearly = Column(DECIMAL(10,2), default=0)
    
    # 用量限制（-1 = 無限制）
    max_customers = Column(Integer, default=50)
    max_emails_month = Column(Integer, default=10)
    max_templates = Column(Integer, default=1)
    max_autominer_runs = Column(Integer, default=5)
    
    # 功能開關
    feature_ai_email = Column(Boolean, default=False)
    feature_attachments = Column(Boolean, default=False)
    feature_click_track = Column(Boolean, default=False)
    feature_open_track = Column(Boolean, default=True)
    feature_hunter_io = Column(Boolean, default=False)
    feature_api_access = Column(Boolean, default=False)
    feature_csv_import = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "price_monthly": float(self.price_monthly or 0),
            "price_yearly": float(self.price_yearly or 0),
            "max_customers": self.max_customers,
            "max_emails_month": self.max_emails_month,
            "max_templates": self.max_templates,
            "max_autominer_runs": self.max_autominer_runs,
            "features": {
                "ai_email": self.feature_ai_email,
                "attachments": self.feature_attachments,
                "click_track": self.feature_click_track,
                "open_track": self.feature_open_track,
                "hunter_io": self.feature_hunter_io,
                "api_access": self.feature_api_access,
                "csv_import": self.feature_csv_import,
            },
            "is_active": self.is_active
        }


# ══════════════════════════════════════════
# Users（使用者帳號）
# ══════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    company_name = Column(String(200))
    role = Column(String(20), default='user')  # 'user', 'admin'
    
    # 狀態
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verify_token = Column(String(255))
    
    # 重設密碼
    reset_token = Column(String(255))
    reset_expires = Column(DateTime)
    
    # 時間戳
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "company_name": self.company_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_sensitive:
            data["last_login_at"] = self.last_login_at.isoformat() if self.last_login_at else None
        return data


# ══════════════════════════════════════════
# Sessions（登入 Session）
# ══════════════════════════════════════════

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 裝置資訊
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # 時間
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="sessions")
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    @staticmethod
    def create_for_user(user_id: int, ip_address=None, user_agent=None, days=30):
        """Create a new session for user"""
        return Session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=days)
        )


# ══════════════════════════════════════════
# Subscriptions（訂閱紀錄）
# ══════════════════════════════════════════

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    
    status = Column(String(20), default='active')  # 'active', 'cancelled', 'expired', 'trial', 'past_due'
    billing_cycle = Column(String(10), default='monthly')  # 'monthly', 'yearly'
    
    # 訂閱週期
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    
    # 試用期
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    
    # 金流（預留）
    payment_provider = Column(String(50))  # 'stripe', 'ecpay', 'manual'
    payment_subscription_id = Column(String(255))
    payment_customer_id = Column(String(255))
    
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan")
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        if self.status not in ['active', 'trial']:
            return False
        if self.current_period_end and datetime.utcnow() > self.current_period_end:
            return False
        return True
    
    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "plan": self.plan.to_dict() if self.plan else None,
            "status": self.status,
            "billing_cycle": self.billing_cycle,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "is_active": self.is_active()
        }


# ══════════════════════════════════════════
# UsageLogs（每月用量追蹤）
# ══════════════════════════════════════════

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 統計週期
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    
    # 用量計數
    customers_count = Column(Integer, default=0)
    emails_sent_count = Column(Integer, default=0)
    autominer_runs_count = Column(Integer, default=0)
    templates_count = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 確保每個 user 每月只有一筆記錄
    __table_args__ = (
        UniqueConstraint('user_id', 'period_year', 'period_month', name='uq_user_period'),
    )
    
    @staticmethod
    def get_or_create(db, user_id: int):
        """Get or create usage log for current month"""
        now = datetime.utcnow()
        log = db.query(UsageLog).filter(
            UsageLog.user_id == user_id,
            UsageLog.period_year == now.year,
            UsageLog.period_month == now.month
        ).first()
        
        if not log:
            log = UsageLog(
                user_id=user_id,
                period_year=now.year,
                period_month=now.month
            )
            db.add(log)
            db.commit()
            db.refresh(log)
        
        return log
    
    def to_dict(self, plan: Plan = None):
        data = {
            "customers": {
                "used": self.customers_count,
                "limit": plan.max_customers if plan else -1
            },
            "emails_month": {
                "used": self.emails_sent_count,
                "limit": plan.max_emails_month if plan else -1
            },
            "autominer_runs": {
                "used": self.autominer_runs_count,
                "limit": plan.max_autominer_runs if plan else -1
            },
            "templates": {
                "used": self.templates_count,
                "limit": plan.max_templates if plan else -1
            }
        }
        return data


# ══════════════════════════════════════════
# 以下是原有的模型（已加入 user_id）
# ══════════════════════════════════════════

# Pricing configuration (legacy, kept for compatibility)
pricing_config = {
    "base_fee": 1000,
    "per_lead": 50,
    "email_open_track": 10,
    "email_click_track": 15,
    "per_lead_usd": 1.5,
}


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 新增
    company_name = Column(String, index=True)
    website_url = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    email_candidates = Column(String, nullable=True)
    mx_valid = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    extracted_keywords = Column(String, nullable=True)
    ai_tag = Column(String, nullable=True)
    status = Column(String, default="Scraped")
    assigned_bd = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Email tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    # Contact person info
    contact_name = Column(String, nullable=True)
    contact_role = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_confidence = Column(Integer, default=0)
    
    # Company details
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    categories = Column(String, nullable=True)
    source_domain = Column(String, nullable=True)
    scrape_location = Column(String, nullable=True)
    
    # Company size indicators
    employee_count = Column(String, nullable=True)
    revenue_range = Column(String, nullable=True)

    email_campaigns = relationship("EmailCampaign", back_populates="lead")


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 新增
    lead_id = Column(Integer, ForeignKey("leads.id"))
    subject = Column(String)
    content = Column(Text)
    status = Column(String, default="Draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="email_campaigns")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 新增
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    attachment_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 新增
    log_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    status = Column(String(50), default="pending")
    
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)
    
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
    clicked_urls = Column(Text, nullable=True)
    
    replied = Column(Boolean, default=False)
    replied_at = Column(DateTime, nullable=True)
    reply_source = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lead = relationship("Lead")
    template = relationship("EmailTemplate")
