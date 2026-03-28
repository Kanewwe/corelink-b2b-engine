"""
Linkora Subscription System - Database Models
包含：users, sessions, subscriptions, plans, usage_logs

v2.7.2: 時區統一處理
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timedelta, timezone
import uuid
import bcrypt

# 台灣時區 (GMT+8)
TAIPEI_TZ = timezone(timedelta(hours=8))

def _now_utc():
    """取得當前 UTC 時間"""
    return datetime.now(timezone.utc)

def _now_utc_naive():
    """取得當前 UTC 時間 (無時區，用於 DB 相容)"""
    return datetime.utcnow()

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
    role = Column(String(20), default='member')  # 'admin', 'vendor', 'member'
    # vendor_id removed - Vendor is now a separate role, not a manager of members
    
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
    smtp_settings = relationship("SMTPSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    email_channel_settings = relationship("EmailChannelSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
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
        """
        Get or create usage log for current month.
        v2.7.2: 使用台灣時間計算年月，確保用量週期與使用者時區一致。
        """
        # 使用台灣時間計算週期
        now_taipei = datetime.now(TAIPEI_TZ)
        year = now_taipei.year
        month = now_taipei.month
        
        log = db.query(UsageLog).filter(
            UsageLog.user_id == user_id,
            UsageLog.period_year == year,
            UsageLog.period_month == month
        ).first()
        
        if not log:
            log = UsageLog(
                user_id=user_id,
                period_year=year,
                period_month=month
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
# SMTP Settings（SMTP 設定）
# ══════════════════════════════════════════

class SMTPSettings(Base):
    __tablename__ = "smtp_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)
    smtp_encryption = Column(String(10), default='tls') # 'tls', 'ssl', 'none'
    
    from_email = Column(String(255))
    from_name = Column(String(255))
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="smtp_settings")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_user": self.smtp_user,
            "smtp_encryption": self.smtp_encryption,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# ══════════════════════════════════════════
# Email Channel Settings (v3.5 Postmark)
# ══════════════════════════════════════════

class EmailChannelSettings(Base):
    __tablename__ = "email_channel_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    provider = Column(String(50), default="postmark") # 'smtp', 'postmark', 'resend'
    
    # Postmark specific
    api_token = Column(String(255), nullable=True) # Usually Encrypted in production
    message_stream = Column(String(50), default="outbound")
    
    # Common identity
    from_email = Column(String(255), nullable=True)
    from_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="email_channel_settings")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "api_token": self.api_token,
            "message_stream": self.message_stream,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


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

class ScrapeTask(Base):
    """Tracks background scraping jobs for Search History UI"""
    __tablename__ = "scrape_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    market = Column(String(50))
    keywords = Column(String(255))
    miner_mode = Column(String(50))
    pages_requested = Column(Integer)
    
    status = Column(String(50), default="Running") # Running, Completed, Failed
    leads_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 關聯日誌
    logs = relationship("ScrapeLog", back_populates="task", order_by="ScrapeLog.id")

    def to_dict(self, include_logs=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "market": self.market,
            "keywords": self.keywords,
            "miner_mode": self.miner_mode,
            "pages_requested": self.pages_requested,
            "status": self.status,
            "leads_found": self.leads_found or 0,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_logs:
            data["logs"] = [log.to_dict() for log in self.logs]
        return data


class ScrapeLog(Base):
    """Detailed log entries for scraping tasks"""
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scrape_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    level = Column(String(20), default="info")  # info, warning, error, success
    message = Column(Text, nullable=False)
    
    # 可選的元數據
    keyword = Column(String(255), nullable=True)
    page = Column(Integer, nullable=True)
    items_found = Column(Integer, nullable=True)
    
    # SA v3.4: Health Tracking
    response_time = Column(DECIMAL(10,3), nullable=True) # Seconds
    http_status = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("ScrapeTask", back_populates="logs")

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "level": self.level,
            "message": self.message,
            "keyword": self.keyword,
            "page": self.page,
            "items_found": self.items_found,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Vendor(Base):
    """Business Vendors (Outsourcing Partners) managed by Admin"""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    company_name = Column(String(200))
    contact_name = Column(String(100))
    contact_phone = Column(String(50))
    
    # 定價結構 (JSON) - 批發價 (Wholesale Price)
    # 格式: {"per_lead": 50, ...}
    pricing_config = Column(Text, default='{}')
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯到使用者帳號
    user = relationship("User")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "pricing_config": json.loads(self.pricing_config or '{}'),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
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
    
    # v3.0: User Overlay Layer (Overrides for Canonical Facts)
    override_name = Column(String(200), nullable=True)
    override_email = Column(String(255), nullable=True)
    personal_notes = Column(Text, nullable=True)
    custom_tags = Column(String(255), nullable=True)
    
    # Email tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_source = Column(String, nullable=True)  # 'free', 'hunter', 'manual'
    
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

    # v3.0: 產業分類沉澱 (Canonical Industry)
    industry_taxonomy = Column(String(255), nullable=True)
    
    # v3.2: AI 評分與情報
    ai_score = Column(Integer, default=0)  # 0-100 分
    ai_score_tags = Column(String(255), nullable=True)  # JSON array: ["高匹配","有信箱"]
    ai_brief = Column(Text, nullable=True)  # AI 生成的公司簡介
    ai_suggestions = Column(Text, nullable=True)  # AI 建議切入點 (JSON)
    ai_scored_at = Column(DateTime, nullable=True)  # 最後評分時間

    # 關聯到全域池 (Global Pool)
    global_id = Column(Integer, ForeignKey("global_leads.id"), nullable=True)

    # 關聯到使用者 (v3.1)
    user = relationship("User", backref="leads")

    email_campaigns = relationship("EmailCampaign", back_populates="lead")

    def to_dict(self):
        # v3.0: 實作「顯示優先權」邏輯 (Personal Overrides > Canonical Facts)
        effective_name = self.override_name or self.company_name
        effective_email = self.override_email or self.contact_email
        
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_name": self.company_name, # Canonical
            "website_url": self.website_url,
            "domain": self.domain,
            "description": self.description,
            "ai_tag": self.ai_tag,
            "industry_taxonomy": self.industry_taxonomy, # v3.0
            "status": self.status,
            "assigned_bd": self.assigned_bd,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_email": self.user.email if self.user else "Hidden/System", # v3.1
            
            # v3.0 Effective Fields (Frontend 優先顯示這些)
            "display_name": effective_name,
            "display_email": effective_email,
            "is_overridden": True if (self.override_name or self.override_email) else False,
            
            # v3.0 Overlays
            "override_name": self.override_name,
            "override_email": self.override_email,
            "personal_notes": self.personal_notes,
            "custom_tags": self.custom_tags,
            
            # Contact info
            "contact_name": self.contact_name,
            "contact_role": self.contact_role,
            "contact_email": self.contact_email, # Canonical
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            
            # Meta
            "global_id": self.global_id,
            "email_sent": self.email_sent,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None
        }


class GlobalLead(Base):
    """
    全域隔離資料池 (Lead Isolation Pool)
    存放全系統唯一的公司資訊，供所有使用者共享參考。
    """
    __tablename__ = "global_leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), index=True)
    domain = Column(String(100), index=True, unique=True) # Domain 是唯一鍵
    website_url = Column(String(500))
    description = Column(Text)
    
    # 聯絡資訊
    contact_email = Column(String(255))
    email_candidates = Column(Text)
    phone = Column(String(50))
    address = Column(Text)
    
    # AI 標籤與產業別
    ai_tag = Column(String(100))
    industry = Column(String(100))
    industry_taxonomy = Column(String(255)) # v3.0: 結構化產業路徑
    
    # v3.0: Fact Quality
    is_verified = Column(Boolean, default=False)
    confidence_score = Column(Integer, default=0)
    
    source = Column(String(100)) # e.g., 'apify_thomasnet', 'apify_yellowpages'
    
    last_scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "domain": self.domain,
            "website_url": self.website_url,
            "description": self.description,
            "contact_email": self.contact_email,
            "email_candidates": self.email_candidates,
            "phone": self.phone,
            "address": self.address,
            "ai_tag": self.ai_tag,
            "industry": self.industry,
            "industry_taxonomy": self.industry_taxonomy,
            "is_verified": self.is_verified,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "last_scraped_at": self.last_scraped_at.isoformat() if self.last_scraped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class GlobalProposal(Base):
    """
    資料修正提案 (v3.0)
    使用者針對全域資料提出的修改建議內容。
    """
    __tablename__ = "global_proposals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    global_id = Column(Integer, ForeignKey("global_leads.id", ondelete="CASCADE"))
    
    field_name = Column(String(100)) # e.g., 'company_name', 'industry'
    current_value = Column(Text)
    suggested_value = Column(Text)
    
    status = Column(String(20), default="Pending") # 'Pending', 'Approved', 'Rejected'
    reason = Column(String(255)) # 拒絕理由或補充說明
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # 關聯
    user = relationship("User")
    global_lead = relationship("GlobalLead")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "System",
            "global_id": self.global_id,
            "global_company_name": self.global_lead.company_name if self.global_lead else "Deleted",
            "field_name": self.field_name,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "status": self.status,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


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

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lead_id": self.lead_id,
            "subject": self.subject,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "tag": self.tag,
            "subject": self.subject,
            "body": self.body,
            "is_default": self.is_default,
            "attachment_url": self.attachment_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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
    
    # SA v3.5: AI Reply Analysis
    reply_intent = Column(String(50), nullable=True)
    reply_analysis = Column(Text, nullable=True)
    reply_next_action = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lead = relationship("Lead")
    template = relationship("EmailTemplate")

    def to_dict(self):
        return {
            "id": self.id,
            "log_uuid": self.log_uuid,
            "lead_id": self.lead_id,
            "recipient": self.recipient,
            "subject": self.subject,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "opened": self.opened,
            "open_count": self.open_count,
            "clicked": self.clicked,
            "replied": self.replied,
            "reply_intent": self.reply_intent,
            "reply_analysis": self.reply_analysis,
            "reply_next_action": self.reply_next_action
        }

class SystemSetting(Base):
    """General key-value storage for system-wide or user-specific settings (e.g., Variable Mapping)"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    key = Column(String(100), nullable=False)   # e.g., 'variable_mapping'
    value = Column(Text)                         # JSON string storage
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 確保每個 user 的 key 是唯一的
    __table_args__ = (
        UniqueConstraint('user_id', 'key', name='uq_user_setting_key'),
    )

    def to_dict(self):
        import json
        try:
            val = json.loads(self.value or '{}')
        except:
            val = self.value
            
        return {
            "key": self.key,
            "value": val,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# ══════════════════════════════════════════
# TransactionLogs（點數交易紀錄 v3.5）
# ══════════════════════════════════════════

class TransactionLog(Base):
    __tablename__ = "transaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type = Column(String(50), nullable=False) # 'scrape', 'ai_intelligence', 'email_dispatch', 'recharge'
    point_delta = Column(Integer, nullable=False) # 負數代表消耗，正數代表充值
    
    # 關聯元數據 (可選)
    task_id = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "point_delta": self.point_delta,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
# ══════════════════════════════════════════
# InboundEmails（收件匣回信 v3.7）
# ══════════════════════════════════════════

class InboundEmail(Base):
    __tablename__ = "inbound_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    
    message_id = Column(String(255), unique=True, index=True) # Postmark MessageID
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    subject = Column(String(512))
    
    body_text = Column(Text)
    body_html = Column(Text)
    
    # AI 分析預存
    reply_intent = Column(String(50), nullable=True)
    ai_draft_suggested = Column(Text, nullable=True)
    
    status = Column(String(20), default="unread") # 'unread', 'read', 'archived', 'replied'
    
    received_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯
    user = relationship("User")
    lead = relationship("Lead")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lead_id": self.lead_id,
            "lead": self.lead.to_dict() if self.lead else None,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "reply_intent": self.reply_intent,
            "ai_draft_suggested": self.ai_draft_suggested,
            "status": self.status,
            "received_at": self.received_at.isoformat() if self.received_at else None
        }
