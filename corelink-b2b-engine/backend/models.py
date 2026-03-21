from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    website_url = Column(String, nullable=True)
    domain = Column(String, nullable=True)  # NEW: discovered domain
    email_candidates = Column(String, nullable=True)  # NEW: comma-separated email candidates
    mx_valid = Column(Integer, default=0)  # NEW: 1 if MX record exists
    description = Column(Text, nullable=True)
    extracted_keywords = Column(String, nullable=True)
    ai_tag = Column(String, nullable=True)  # NA-CABLE, NA-NAMEPLATE, NA-PLASTIC
    status = Column(String, default="Scraped")
    assigned_bd = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    email_campaigns = relationship("EmailCampaign", back_populates="lead")

class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    subject = Column(String)
    content = Column(Text)
    status = Column(String, default="Draft")  # Draft, Sent
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="email_campaigns")
