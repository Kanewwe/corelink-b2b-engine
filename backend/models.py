from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

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
    
    # NEW: Contact person info (角色定向)
    contact_name = Column(String, nullable=True)      # 聯絡人姓名 (John Smith)
    contact_role = Column(String, nullable=True)      # 角色 (Procurement Manager)
    contact_email = Column(String, nullable=True)     # 聯絡人 Email
    contact_confidence = Column(Integer, default=0)   # Hunter confidence score
    
    # NEW: Company details (從黃頁直接抓)
    phone = Column(String, nullable=True)             # 公司電話
    address = Column(String, nullable=True)           # 公司地址
    city = Column(String, nullable=True)              # 城市
    state = Column(String, nullable=True)             # 州/省
    zip_code = Column(String, nullable=True)          # 郵遞區號
    categories = Column(String, nullable=True)        # 產業類別
    source_domain = Column(String, nullable=True)     # 來源目錄 (yellowpages.com)
    scrape_location = Column(String, nullable=True)   # 爬取地區
    
    # NEW: Company size indicators
    employee_count = Column(String, nullable=True)    # 員工數
    revenue_range = Column(String, nullable=True)     # 營收範圍

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

# Engagement tracking model
class EmailEngagement(Base):
    __tablename__ = "email_engagements"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("email_campaigns.id"))
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    tracked_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("EmailCampaign", backref="engagements")
