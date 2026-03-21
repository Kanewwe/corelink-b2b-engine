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
    # Startup Events
    email_sender_job.start_scheduler()
    yield
    # Shutdown logic...

app = FastAPI(title="Corelink B2B Engine API (Optimized)", lifespan=lifespan)

# Setup CORS to allow the frontend to access the API
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

# --- Authentication Logic ---
security = HTTPBearer()

# SECURITY FIX: Load credentials from environment
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
    """Authenticate user and return API token."""
    expected_user = os.getenv("ADMIN_USER", "admin")
    expected_pass = os.getenv("ADMIN_PASSWORD", "changeme")
    
    if req.username == expected_user and req.password == expected_pass:
        return {"token": API_TOKEN, "username": req.username}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# --- API Endpoints ---

@app.post("/api/leads", response_model=LeadResponse)
def create_and_tag_lead(lead: LeadCreateReq, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    """Create a new lead with rule-based classification."""
    # 1. Rule-based classification (no GPT)
    tag_result = ai_service.analyze_company_and_tag(lead.company_name, lead.description, use_gpt=False)
    
    # 2. Extract Keywords
    keywords_list = tag_result.get("Keywords", [])
    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

    # 3. Auto-discover email
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
    """Get all leads."""
    return db.query(models.Lead).order_by(models.Lead.id.desc()).all()

@app.post("/api/leads/{lead_id}/generate-email", response_model=EmailCampaignResponse)
def generate_email_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    """Generate personalized email for a lead."""
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Generate email using GPT (creative writing needed)
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
    """Get all emails for a lead."""
    return db.query(models.EmailCampaign).filter(models.EmailCampaign.lead_id == lead_id).all()

@app.get("/api/campaigns", response_model=List[CampaignLogResponse])
def get_all_campaign_logs(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    """Get all email campaign logs."""
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
    """Get system logs."""
    return {"logs": SYSTEM_LOGS}

@app.post("/api/test-email")
def test_email_dispatch(current_user: str = Depends(verify_token)):
    """Test email dispatch."""
    add_log(f"Manual Test Email triggered by {current_user}")
    return {"message": "Test event logged. Check system logs."}

@app.post("/api/scrape")
def trigger_scraper(req: ScrapeRequest, background_tasks: BackgroundTasks, current_user: str = Depends(verify_token)):
    """Trigger background scraping task."""
    import scraper
    background_tasks.add_task(scraper.scrape_and_process_task, req.market, req.keyword)
    return {"message": f"Scraping task for {req.market} {req.keyword} started in the background."}

# --- Health Check ---
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- Static Files Hosting (Serve Frontend) ---
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(frontend_path):
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
