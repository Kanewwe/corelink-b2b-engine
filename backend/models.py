from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

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
    
    # NEW: Track if email has been sent
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)

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
