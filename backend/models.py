from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid

# Pricing configuration (can be stored/edited via API)
pricing_config = {
    "base_fee": 1000,           # 基本費用
    "per_lead": 50,             # 每筆客戶費用
    "email_open_track": 10,     # 開信追蹤費用
    "email_click_track": 15,    # 點擊追蹤費用
    "per_lead_usd": 1.5,        # 每筆客戶美元報價
}

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
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
    
    # Contact person info (角色定向)
    contact_name = Column(String, nullable=True)
    contact_role = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_confidence = Column(Integer, default=0)
    
    # Company details (從黃頁直接抓)
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
    lead_id = Column(Integer, ForeignKey("leads.id"))
    subject = Column(String)
    content = Column(Text)
    status = Column(String, default="Draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="email_campaigns")

# NEW: Email Template Model
class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)  # NA-CABLE, NA-NAMEPLATE, NA-PLASTIC
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    attachment_url = Column(String, nullable=True)  # Optional attachment URL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# NEW: Email Log Model - Full engagement tracking
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic info
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    
    # Timing
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Delivery status
    status = Column(String(50), default="pending")  # pending, delivered, soft_bounce, hard_bounce, failed
    
    # Engagement tracking
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)
    
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
    clicked_urls = Column(JSON, nullable=True)  # [{"url": "...", "count": 1}]
    
    replied = Column(Boolean, default=False)
    replied_at = Column(DateTime, nullable=True)
    reply_source = Column(String(50), nullable=True)  # manual, imap, webhook
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead")
    template = relationship("EmailTemplate")
