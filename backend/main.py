from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

from database import engine, Base, get_db
import models
import ai_service
from contextlib import asynccontextmanager
import email_sender_job
from logger import add_log, SYSTEM_LOGS

# Create database tables automatically
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Events — scheduler auto-start is disabled by default (EMAIL_SCHEDULER_ENABLED=false)
    # Use POST /api/scheduler/start to manually enable it
    yield

app = FastAPI(title="Corelink B2B Engine API (Optimized)", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class LeadCreateReq(BaseModel):
    company_name: str
    website_url: str = None
    description: str

class ScrapeRequest(BaseModel):
    market: str
    keyword: str

class LoginReq(BaseModel):
    username: str
    password: str

class CampaignLogResponse(BaseModel):
    id: int
    lead_id: int
    company_name: str
    assigned_bd: str
    subject: str
    content: str
    status: str
    created_at: str
    model_config = {"from_attributes": True}

class LeadResponse(BaseModel):
    id: int
    company_name: str
    website_url: Optional[str] = None
    domain: Optional[str] = None
    email_candidates: Optional[str] = None
    mx_valid: int = 0
    ai_tag: str
    assigned_bd: str
    extracted_keywords: Optional[str] = None
    status: str
    model_config = {"from_attributes": True}

class EmailCampaignResponse(BaseModel):
    id: int
    lead_id: int
    subject: str
    content: str
    status: str
    model_config = {"from_attributes": True}

class EmailTemplateCreate(BaseModel):
    name: str
    tag: str
    subject: str
    body: str
    is_default: bool = False
    attachment_url: Optional[str] = None

class EngagementUpdate(BaseModel):
    opened: bool = False
    clicked: bool = False
    replied: bool = False

class PricingConfigUpdate(BaseModel):
    base_fee: int
    per_lead: int
    email_open_track: int
    email_click_track: int
    per_lead_usd: float

class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    tag: str
    subject: str
    body: str
    is_default: bool
    attachment_url: Optional[str] = None
    created_at: str
    model_config = {"from_attributes": True}

# --- Authentication ---
security = HTTPBearer()

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
API_TOKEN = os.getenv("API_TOKEN", "secure-token-change-me")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.post("/api/login")
def login(req: LoginReq):
    expected_user = os.getenv("ADMIN_USER", "admin")
    expected_pass = os.getenv("ADMIN_PASSWORD", "changeme")
    
    if req.username == expected_user and req.password == expected_pass:
        return {"token": API_TOKEN, "username": req.username}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# --- Debug Endpoint ---
@app.get("/api/debug")
def debug():
    return {
        "admin_user": os.getenv("ADMIN_USER"),
        "password_set": bool(os.getenv("ADMIN_PASSWORD")),
        "token_set": bool(os.getenv("API_TOKEN")),
        "openai_set": bool(os.getenv("OPENAI_API_KEY")),
        "database_url": os.getenv("DATABASE_URL", "NOT SET"),
    }

# --- API Endpoints ---
@app.post("/api/leads", response_model=LeadResponse)
def create_and_tag_lead(lead: LeadCreateReq, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    tag_result = ai_service.analyze_company_and_tag(lead.company_name, lead.description, use_gpt=False)
    keywords_list = tag_result.get("Keywords", [])
    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

    import email_finder
    import asyncio
    email_info = asyncio.run(email_finder.find_emails_for_company(lead.company_name))

    db_lead = models.Lead(
        company_name=lead.company_name,
        website_url=lead.website_url,
        domain=email_info.get("domain"),
        email_candidates=", ".join(email_info.get("emails", [])) if email_info.get("emails") else None,
        mx_valid=1 if email_info.get("mx_valid") else 0,
        description=lead.description,
        extracted_keywords=keywords_str,
        ai_tag=tag_result.get("Tag", "UNKNOWN"),
        assigned_bd=tag_result.get("BD", "General"),
        status="Tagged"
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@app.get("/api/leads", response_model=List[LeadResponse])
def get_leads(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    return db.query(models.Lead).order_by(models.Lead.id.desc()).all()

@app.post("/api/leads/{lead_id}/generate-email", response_model=EmailCampaignResponse)
def generate_email_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    k_list = [k.strip() for k in lead.extracted_keywords.split(',')] if lead.extracted_keywords else []
    email_result = ai_service.generate_outreach_email(
        lead.company_name, lead.description, lead.ai_tag, lead.assigned_bd, k_list
    )
    
    campaign = models.EmailCampaign(
        lead_id=lead.id,
        subject=email_result.get("Subject", "Outreach from Corelink"),
        content=email_result.get("Body", "Content could not be generated."),
        status="Draft"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    lead.status = "Email_Drafted"
    db.commit()
    
    return campaign

@app.get("/api/leads/{lead_id}/emails", response_model=List[EmailCampaignResponse])
def get_emails_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    return db.query(models.EmailCampaign).filter(models.EmailCampaign.lead_id == lead_id).all()

@app.get("/api/campaigns", response_model=List[CampaignLogResponse])
def get_all_campaign_logs(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    campaigns = db.query(models.EmailCampaign).order_by(models.EmailCampaign.id.desc()).all()
    result = []
    for c in campaigns:
        lead = c.lead
        if lead:
            result.append({
                "id": c.id,
                "lead_id": c.lead_id,
                "company_name": lead.company_name,
                "assigned_bd": lead.assigned_bd,
                "subject": c.subject,
                "content": c.content,
                "status": c.status,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else ""
            })
    return result

@app.get("/api/system-logs")
def get_system_logs(current_user: str = Depends(verify_token)):
    return {"logs": SYSTEM_LOGS}

@app.post("/api/test-email")
def test_email_dispatch(current_user: str = Depends(verify_token)):
    add_log(f"Manual Test Email triggered by {current_user}")
    return {"message": "Test event logged. Check system logs."}

# --- Scheduler Control Endpoints ---
@app.post("/api/scheduler/start")
def start_scheduler(current_user: str = Depends(verify_token)):
    email_sender_job.start_scheduler()
    status = email_sender_job.get_scheduler_status()
    return {"message": "Scheduler started", "status": status}

@app.post("/api/scheduler/stop")
def stop_scheduler(current_user: str = Depends(verify_token)):
    stopped = email_sender_job.stop_scheduler()
    status = email_sender_job.get_scheduler_status()
    return {"message": "Scheduler stopped" if stopped else "Scheduler was not running", "status": status}

@app.get("/api/scheduler/status")
def get_scheduler_status(current_user: str = Depends(verify_token)):
    return email_sender_job.get_scheduler_status()

@app.post("/api/scrape")
def trigger_scraper(req: ScrapeRequest, background_tasks: BackgroundTasks, current_user: str = Depends(verify_token)):
    import scraper
    background_tasks.add_task(scraper.scrape_and_process_task, req.market, req.keyword)
    return {"message": f"Scraping task for {req.market} {req.keyword} started."}

class ScrapeSimpleRequest(BaseModel):
    market: str = "US"
    pages: int = 3

@app.post("/api/scrape-simple")

@app.post("/api/scrape-simple")
def trigger_scrape_simple(req: ScrapeSimpleRequest, background_tasks: BackgroundTasks, current_user: str = Depends(verify_token)):
    """Simplified scraper using Yahoo search dorking + email finder."""
    import scrape_simple as scrape_mod
    background_tasks.add_task(scrape_mod.scrape_simple, req.market, req.pages)
    return {"message": f"Simple scrape started for market={req.market}"}

def get_templates(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    templates = db.query(models.EmailTemplate).order_by(models.EmailTemplate.tag, models.EmailTemplate.name).all()
    return templates

@app.post("/api/templates", response_model=EmailTemplateResponse)
def create_template(template: EmailTemplateCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_template = models.EmailTemplate(
        name=template.name,
        tag=template.tag,
        subject=template.subject,
        body=template.body,
        is_default=template.is_default,
        attachment_url=template.attachment_url
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    add_log(f"✉️ [模板] 新增模板: {template.name} ({template.tag})")
    return db_template

@app.put("/api/templates/{template_id}", response_model=EmailTemplateResponse)
def update_template(template_id: int, template: EmailTemplateCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_template = db.query(models.EmailTemplate).filter(models.EmailTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_template.name = template.name
    db_template.tag = template.tag
    db_template.subject = template.subject
    db_template.body = template.body
    db_template.is_default = template.is_default
    db_template.attachment_url = template.attachment_url
    db_template.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_template)
    return db_template

@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_template = db.query(models.EmailTemplate).filter(models.EmailTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    return {"message": "Template deleted"}

# --- Email Sent Tracking ---
@app.post("/api/leads/{lead_id}/mark-sent")
def mark_email_sent(lead_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.email_sent = True
    lead.email_sent_at = datetime.utcnow()
    db.commit()
    
    add_log(f"📧 [寄信] 標記已寄信: {lead.company_name}")
    return {"message": "Email marked as sent"}

# --- Email Engagement Tracking ---
@app.get("/api/engagements")
def get_engagements(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    """取得所有追蹤資料，含標籤維度的統計"""
    engagements = db.query(models.EmailEngagement).all()
    campaigns = db.query(models.EmailCampaign).all()
    leads = db.query(models.Lead).all()

    # Build lookup maps
    campaign_map = {c.id: c for c in campaigns}
    lead_map = {l.id: l for l in leads}

    # Group by tag (industry)
    tag_stats = {}
    for e in engagements:
        campaign = campaign_map.get(e.campaign_id)
        if not campaign:
            continue
        lead = lead_map.get(campaign.lead_id)
        tag = lead.ai_tag if lead and lead.ai_tag else "UNKNOWN"

        if tag not in tag_stats:
            tag_stats[tag] = {"total": 0, "opened": 0, "clicked": 0, "replied": 0}

        tag_stats[tag]["total"] += 1
        if e.opened:
            tag_stats[tag]["opened"] += 1
        if e.clicked:
            tag_stats[tag]["clicked"] += 1
        if e.replied:
            tag_stats[tag]["replied"] += 1

    # Individual records
    records = []
    for e in engagements:
        campaign = campaign_map.get(e.campaign_id)
        if not campaign:
            continue
        lead = lead_map.get(campaign.lead_id)
        records.append({
            "id": e.id,
            "campaign_id": e.campaign_id,
            "company_name": lead.company_name if lead else "N/A",
            "ai_tag": lead.ai_tag if lead else "UNKNOWN",
            "opened": e.opened,
            "clicked": e.clicked,
            "replied": e.replied,
            "tracked_at": e.tracked_at.strftime("%Y-%m-%d %H:%M:%S") if e.tracked_at else ""
        })

    return {
        "records": records,
        "tag_stats": tag_stats,
        "total_leads": db.query(models.Lead).count(),
        "total_campaigns": len(campaigns),
    }

@app.post("/api/engagements/{campaign_id}")
def update_engagement(campaign_id: int, update: EngagementUpdate, db: Session = Depends(get_db)):
    """
    更新或建立追蹤狀態（可被外部郵件追蹤像素呼叫，無需認證以支援追蹤）
    """
    engagement = db.query(models.EmailEngagement).filter(
        models.EmailEngagement.campaign_id == campaign_id
    ).first()

    if not engagement:
        engagement = models.EmailEngagement(
            campaign_id=campaign_id,
            opened=update.opened,
            clicked=update.clicked,
            replied=update.replied,
            tracked_at=datetime.utcnow()
        )
        db.add(engagement)
    else:
        if update.opened:
            engagement.opened = True
        if update.clicked:
            engagement.clicked = True
        if update.replied:
            engagement.replied = True
        engagement.tracked_at = datetime.utcnow()

    db.commit()
    return {"message": "Engagement updated"}

# --- Pricing Config ---
@app.get("/api/pricing")
def get_pricing(current_user: str = Depends(verify_token)):
    return models.pricing_config

@app.put("/api/pricing")
def update_pricing(config: PricingConfigUpdate, current_user: str = Depends(verify_token)):
    models.pricing_config.update(config.model_dump())
    add_log(f"💰 收費標準已更新: {config.model_dump()}")
    return {"message": "Pricing updated", "config": models.pricing_config}

# --- Health Check ---
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "admin_user": os.getenv("ADMIN_USER", "none"),
        "admin_password_set": bool(os.getenv("ADMIN_PASSWORD")),
        "database_url": os.getenv("DATABASE_URL", "NOT SET"),
    }

# --- Static Files Hosting ---
possible_paths = [
    os.path.join(os.path.dirname(__file__), "frontend"),
    os.path.join(os.path.dirname(__file__), "..", "frontend"),
    "/app/frontend",
]

frontend_path = None
for path in possible_paths:
    if os.path.exists(path):
        frontend_path = path
        break

if frontend_path and os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def read_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
    
    @app.get("/{file_path}")
    async def serve_file(file_path: str):
        full_path = os.path.join(frontend_path, file_path)
        if os.path.isfile(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Corelink API is running. Frontend folder not found."}

# DEBUG: Test scrape directly
@app.post("/api/debug-scrape")
def debug_scrape(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    import scrape_simple
    try:
        scrape_simple.scrape_simple("US", 1)
        return {"message": "Scrape completed"}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}
