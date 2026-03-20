from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import engine, Base, get_db
import models
import ai_service

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Corelink B2B Engine API")

# Setup CORS to allow the frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for Request/Response
class LeadCreateReq(BaseModel):
    company_name: str
    website_url: str = None
    description: str

class ScrapeRequest(BaseModel):
    search_url: str
    max_pages: int = 1

class LoginReq(BaseModel):
    username: str
    password: str

# --- Authentication Logic ---
security = HTTPBearer()

USERS = {
    "KaneXiao": "admin123",
    "JasonXiao": "admin123"
}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in ["KaneXiao-token", "JasonXiao-token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.split("-")[0]

@app.post("/api/login")
def login(req: LoginReq):
    if req.username in USERS and USERS[req.username] == req.password:
        return {"token": f"{req.username}-token", "username": req.username}
    raise HTTPException(status_code=401, detail="Invalid username or password")

class LeadResponse(BaseModel):
    id: int
    company_name: str
    ai_tag: str
    assigned_bd: str
    extracted_keywords: str = None
    status: str

    class Config:
        orm_mode = True

class EmailCampaignResponse(BaseModel):
    id: int
    lead_id: int
    subject: str
    content: str
    status: str

    class Config:
        orm_mode = True

# API Endpoints
@app.post("/api/leads", response_model=LeadResponse)
def create_and_tag_lead(lead: LeadCreateReq, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    # 1. Ask AI to analyze the company and assign a Tag & BD
    tag_result = ai_service.analyze_company_and_tag(lead.company_name, lead.description)
    
    # 2. Extract Keywords and Save to SQLite DB
    keywords_list = tag_result.get("Keywords", [])
    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

    db_lead = models.Lead(
        company_name=lead.company_name,
        website_url=lead.website_url,
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
        
    # Generate Highly-Personalized Email Draft using AI
    k_list = [k.strip() for k in lead.extracted_keywords.split(',')] if lead.extracted_keywords else []
    email_result = ai_service.generate_outreach_email(
        lead.company_name, lead.description, lead.ai_tag, lead.assigned_bd, k_list
    )
    
    # Save Campaign to DB
    campaign = models.EmailCampaign(
        lead_id=lead.id,
        subject=email_result.get("Subject", "Outreach from Corelink"),
        content=email_result.get("Body", "Content could not be generated."),
        status="Draft"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Update Lead status
    lead.status = "Email_Drafted"
    db.commit()
    
    return campaign

@app.get("/api/leads/{lead_id}/emails", response_model=List[EmailCampaignResponse])
def get_emails_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    return db.query(models.EmailCampaign).filter(models.EmailCampaign.lead_id == lead_id).all()

@app.post("/api/scrape")
def trigger_scraper(req: ScrapeRequest, background_tasks: BackgroundTasks, current_user: str = Depends(verify_token)):
    import scraper
    background_tasks.add_task(scraper.scrape_and_process_task, req.search_url, req.max_pages)
    return {"message": f"Scraping task for {req.search_url} started in the background."}
