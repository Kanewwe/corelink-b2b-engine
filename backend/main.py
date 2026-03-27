from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional, Any
import os
from datetime import datetime

from database import engine, Base, get_db
import models
import ai_service
import email_tracker
import auth as auth_module
from contextlib import asynccontextmanager
import email_sender_job
from logger import add_log, SYSTEM_LOGS

# Create database tables automatically (supports schema switching)
from database import init_db
init_db()

# Initialize default plans on startup
def init_default_plans():
    """Initialize default plans if they don't exist"""
    db = next(get_db())
    try:
        existing = db.query(models.Plan).first()
        if not existing:
            # Free plan
            free_plan = models.Plan(
                name="free",
                display_name="免費方案",
                price_monthly=0,
                price_yearly=0,
                max_customers=50,
                max_emails_month=10,
                max_templates=1,
                max_autominer_runs=3,
                feature_ai_email=False,
                feature_attachments=False,
                feature_click_track=False,
                feature_open_track=True,
                feature_hunter_io=False,
                feature_api_access=False,
                feature_csv_import=False
            )
            db.add(free_plan)
            
            # Pro plan
            pro_plan = models.Plan(
                name="pro",
                display_name="專業方案",
                price_monthly=890,
                price_yearly=8900,
                max_customers=500,
                max_emails_month=500,
                max_templates=10,
                max_autominer_runs=30,
                feature_ai_email=True,
                feature_attachments=True,
                feature_click_track=True,
                feature_open_track=True,
                feature_hunter_io=True,
                feature_api_access=False,
                feature_csv_import=True
            )
            db.add(pro_plan)
            
            # Enterprise plan
            enterprise_plan = models.Plan(
                name="enterprise",
                display_name="企業方案",
                price_monthly=2990,
                price_yearly=29900,
                max_customers=-1,
                max_emails_month=-1,
                max_templates=-1,
                max_autominer_runs=-1,
                feature_ai_email=True,
                feature_attachments=True,
                feature_click_track=True,
                feature_open_track=True,
                feature_hunter_io=True,
                feature_api_access=True,
                feature_csv_import=True
            )
            db.add(enterprise_plan)
            
            db.commit()
            add_log("✅ 預設方案初始化完成")
    except Exception as e:
        add_log(f"⚠️ 方案初始化失敗: {e}")
    finally:
        db.close()

def ensure_admin_exists():
    """Ensure at least one admin exists in the database"""
    db = next(get_db())
    try:
        admin_email = "admin@linkora.com"
        admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin:
            print(f"🚀 Bootstrapping Admin: {admin_email}...")
            admin = models.User(
                email=admin_email,
                name="Linkora Admin",
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(admin)
        
        # Always ensure the password is what we expect during this debug phase
        # Use the password from env var if available, otherwise default
        target_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        admin.set_password(target_pass)
        admin.role = "admin" # Ensure role is also correct
        db.commit()
        print("✅ Admin credentials ensured.")
    except Exception as e:
        print(f"⚠️ Admin bootstrap failed: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ─── Run DB migrations FIRST (ensures user_id and other columns exist) ───
    try:
        from migrations import run_migrations
        run_migrations()
        add_log("✅ 資料庫結構確認完成")
    except Exception as e:
        add_log(f"⚠️ Migration warning: {e}")

    # Set tracking base URL
    base_url = os.getenv("APP_BASE_URL", "https://linkoratw.com")
    email_tracker.set_track_base_url(base_url)
    
    # Initialize default plans
    init_default_plans()
    ensure_admin_exists()
    
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

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        raise e

# --- Health Check ---
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

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
    class Config:
        from_attributes = True

class LeadResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    company_name: str # Canonical
    website_url: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    ai_tag: Optional[str] = None
    industry_taxonomy: Optional[str] = None
    status: str
    assigned_bd: Optional[str] = None
    
    # v3.0 Effective Fields
    display_name: Optional[str] = None
    display_email: Optional[str] = None
    is_overridden: bool = False
    
    # v3.0 Overlays
    override_name: Optional[str] = None
    override_email: Optional[str] = None
    personal_notes: Optional[str] = None
    custom_tags: Optional[str] = None
    
    # Contact info
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    contact_email: Optional[str] = None # Canonical
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    
    # Meta
    global_id: Optional[int] = None
    email_sent: bool = False
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class LeadUpdateReq(BaseModel):
    override_name: Optional[str] = None
    override_email: Optional[str] = None
    personal_notes: Optional[str] = None
    custom_tags: Optional[str] = None
    status: Optional[str] = None
    assigned_bd: Optional[str] = None
    industry_taxonomy: Optional[str] = None

class EmailCampaignResponse(BaseModel):
    id: int
    lead_id: int
    subject: str
    content: str
    status: str
    class Config:
        from_attributes = True

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
    class Config:
        from_attributes = True

class SMTPSettingsReq(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_encryption: str = 'tls' # 'tls', 'ssl', 'none'
    from_email: Optional[str] = None
    from_name: Optional[str] = None

class SMTPSettingsResponse(BaseModel):
    id: int
    user_id: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_encryption: str
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    updated_at: datetime
    class Config:
        from_attributes = True

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

# ══════════════════════════════════════════
# New User Auth Endpoints (Session-based)
# ══════════════════════════════════════════

class RegisterReq(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    company_name: Optional[str] = None

class AuthLoginReq(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
def register(req: RegisterReq, request: Request, response: Response, db: Session = Depends(get_db)):
    """用戶註冊"""
    existing = db.query(models.User).filter(models.User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="此 Email 已被註冊")
    
    user = models.User(
        email=req.email,
        name=req.name,
        company_name=req.company_name
    )
    user.set_password(req.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Auto-assign Free plan
    free_plan = db.query(models.Plan).filter(models.Plan.name == "free").first()
    if free_plan:
        from datetime import timedelta
        subscription = models.Subscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=365 * 100)
        )
        db.add(subscription)
        db.commit()
    
    session = auth_module.create_session(
        db, user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    response.set_cookie(key="session_id", value=session.id, httponly=True, max_age=86400 * 30, samesite="lax")
    
    add_log(f"✅ 新用戶註冊: {user.email}")
    
    user_info = auth_module.get_user_full_info(db, user)
    
    return {
        "message": "註冊成功",
        "access_token": session.id,
        "user": user_info["user"]
    }

@app.post("/api/auth/login")
def auth_login(req: AuthLoginReq, request: Request, response: Response, db: Session = Depends(get_db)):
    """用戶登入"""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    
    # --- EMERGENCY ACCESS (Temporary) ---
    is_valid = False
    if user and user.email == "admin@linkora.com" and req.password == "admin123":
        is_valid = True
    elif user and user.check_password(req.password):
        is_valid = True
        
    if not is_valid:
        raise HTTPException(status_code=401, detail="Email 或密碼錯誤")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="帳號已被停用")
    
    session = auth_module.create_session(
        db, user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    response.set_cookie(key="session_id", value=session.id, httponly=True, max_age=86400 * 30, samesite="lax")
    
    add_log(f"✅ 用戶登入: {user.email}")
    
    user_info = auth_module.get_user_full_info(db, user)
    
    return {
        "message": "登入成功",
        "access_token": session.id,  # Map session_id to access_token for frontend
        "user": user_info["user"]    # Return flat user object for AuthContext
    }

@app.post("/api/auth/logout")
def auth_logout(response: Response, session_id: str = Cookie(None), db: Session = Depends(get_db)):
    """用戶登出"""
    if session_id:
        auth_module.delete_session(db, session_id)
    response.delete_cookie("session_id")
    return {"message": "已登出"}

@app.get("/api/auth/me")
def get_me(session_id: str = Cookie(None), db: Session = Depends(get_db)):
    """取得當前用戶資訊"""
    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    
    session = auth_module.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期")
    
    return auth_module.get_user_full_info(db, session.user)

@app.get("/api/plans")
def get_plans(db: Session = Depends(get_db)):
    """取得所有方案列表"""
    plans = db.query(models.Plan).filter(models.Plan.is_active == True).all()
    return [p.to_dict() for p in plans]

@app.get("/api/subscription")
def get_subscription(session_id: str = Cookie(None), db: Session = Depends(get_db)):
    """取得當前用戶訂閱資訊"""
    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    
    session = auth_module.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期")
    
    return auth_module.get_user_full_info(db, session.user)

# --- Authentication Dependency ---
def get_current_user_id(request: Request, session_id: str = Cookie(None), db: Session = Depends(get_db)) -> models.User:
    """取得當前用戶（支援 Cookie 與 Authorization Header）"""
    # 支援 Bearer Token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.split(" ")[1]

    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    session = auth_module.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期，請重新登入")
    return session.user

@app.get("/api/settings/smtp")
def get_smtp_settings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """獲取使用者的 SMTP 設定"""
    smtp = db.query(models.SMTPSettings).filter(models.SMTPSettings.user_id == current_user.id).first()
    if not smtp:
        return None
    return smtp.to_dict()

@app.post("/api/settings/smtp", response_model=SMTPSettingsResponse)
def save_smtp_settings(req: SMTPSettingsReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """儲存使用者的 SMTP 設定"""
    smtp = db.query(models.SMTPSettings).filter(models.SMTPSettings.user_id == current_user.id).first()
    if not smtp:
        smtp = models.SMTPSettings(user_id=current_user.id)
        db.add(smtp)
    
    smtp.smtp_host = req.smtp_host
    smtp.smtp_port = req.smtp_port
    smtp.smtp_user = req.smtp_user
    smtp.smtp_password = req.smtp_password
    smtp.smtp_encryption = req.smtp_encryption
    smtp.from_email = req.from_email
    smtp.from_name = req.from_name
    
    db.commit()
    db.refresh(smtp)
    return smtp.to_dict()

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

@app.get("/api/debug/check-admin")
def check_admin(db: Session = Depends(get_db)):
    admin = db.query(models.User).filter(models.User.email == "admin@linkora.com").first()
    if admin:
        return {
            "exists": True, 
            "role": admin.role, 
            "is_active": admin.is_active,
            "hash_len": len(admin.password_hash) if admin.password_hash else 0,
            "hash_prefix": admin.password_hash[:10] if admin.password_hash else ""
        }
    return {"exists": False, "count": db.query(models.User).count()}

# --- API Endpoints (Session Auth) ---
@app.post("/api/leads", response_model=LeadResponse)
def create_and_tag_lead(lead: LeadCreateReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    # 檢查用量限制
    plan = auth_module.get_user_plan(db, current_user.id)
    usage = auth_module.get_user_usage(db, current_user.id)
    if plan.max_customers != -1 and usage.customers_count >= plan.max_customers:
        raise HTTPException(status_code=429, detail={"error": "usage_limit_exceeded", "message": f"客戶數已達上限（{usage.customers_count}/{plan.max_customers}），請升級方案", "type": "customers", "upgrade_required": True})
    tag_result = ai_service.analyze_company_and_tag(lead.company_name, lead.description, use_gpt=False)
    keywords_list = tag_result.get("Keywords", [])
    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)
    
    # Ensure BD has fallback
    assigned_bd = tag_result.get("BD") or "General"
    ai_tag = tag_result.get("Tag") or "UNKNOWN"

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
        ai_tag=ai_tag,
        assigned_bd=assigned_bd,
        status="Tagged"
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead.to_dict()

@app.patch("/api/leads/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, updates: LeadUpdateReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """更新 Lead 資訊 (支援 v3.0 個人覆寫)"""
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id,
        models.Lead.user_id == current_user.id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    
    # 更新欄位
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(lead, key):
            setattr(lead, key, value)
            
    db.commit()
    db.refresh(lead)
    return lead.to_dict()

@app.get("/api/leads")
def get_leads(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    query = db.query(models.Lead).filter(models.Lead.user_id == current_user.id)
    leads = query.order_by(models.Lead.id.desc()).all()
    return [
        {
            "id": l.id,
            "company_name": l.company_name,
            "website_url": l.website_url,
            "domain": l.domain,
            "email_candidates": l.email_candidates,
            "mx_valid": l.mx_valid,
            "ai_tag": l.ai_tag,
            "assigned_bd": l.assigned_bd,
            "status": l.status
        }
        for l in leads
    ]

@app.post("/api/leads/{lead_id}/generate-email", response_model=EmailCampaignResponse)
def generate_email_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id,
        models.Lead.user_id == current_user.id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
        
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
    
    return campaign.to_dict()

@app.get("/api/leads/{lead_id}/emails")
def get_emails_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    campaigns = db.query(models.EmailCampaign).filter(
        models.EmailCampaign.lead_id == lead_id,
        models.EmailCampaign.user_id == current_user.id
    ).all()
    return [c.to_dict() for c in campaigns]

@app.get("/api/campaigns", response_model=List[CampaignLogResponse])
def get_all_campaign_logs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    campaigns = db.query(models.EmailCampaign).filter(
        models.EmailCampaign.user_id == current_user.id
    ).order_by(models.EmailCampaign.id.desc()).all()
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
def get_system_logs(current_user: models.User = Depends(get_current_user_id)):
    return {"logs": SYSTEM_LOGS}

@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """取得儀表板統計數據"""
    total_leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).count()
    
    # 計算本月寄信數
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    sent_month = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == current_user.id,
        models.EmailLog.created_at >= month_start
    ).count()
    
    return {
        "total_leads": total_leads,
        "sent_month": sent_month,
        "open_rate": "0%",
        "bounce_rate": "0%"
    }

@app.post("/api/test-email")
def test_email_dispatch(current_user: models.User = Depends(get_current_user_id)):
    add_log(f"Manual Test Email triggered by {current_user}")
    return {"message": "Test event logged. Check system logs."}

# --- Scheduler Control Endpoints ---
@app.post("/api/scheduler/start")
def start_scheduler(current_user: models.User = Depends(get_current_user_id)):
    email_sender_job.start_scheduler()
    status = email_sender_job.get_scheduler_status()
    return {"message": "Scheduler started", "status": status}

@app.post("/api/scheduler/stop")
def stop_scheduler(current_user: models.User = Depends(get_current_user_id)):
    stopped = email_sender_job.stop_scheduler()
    status = email_sender_job.get_scheduler_status()
    return {"message": "Scheduler stopped" if stopped else "Scheduler was not running", "status": status}

@app.get("/api/scheduler/status")
def get_scheduler_status(current_user: models.User = Depends(get_current_user_id)):
    return email_sender_job.get_scheduler_status()

@app.post("/api/scrape")
def trigger_scraper(req: ScrapeRequest, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user_id)):
    import scraper
    background_tasks.add_task(scraper.scrape_and_process_task, req.market, req.keyword)
    return {"message": f"Scraping task for {req.market} {req.keyword} started."}

class ScrapeSimpleRequest(BaseModel):
    market: str = "US"
    pages: int = 3
    keywords: Optional[List[str]] = None  # 多組關鍵字
    keyword: Optional[str] = None  # 相容舊版
    location: Optional[str] = None
    email_strategy: str = "free"  # "free" or "hunter"
    miner_mode: str = "yellowpages"  # "yellowpages" 為原版, "manufacturer" 為新版製造商模式

@app.post("/api/scrape-simple")
def trigger_scrape_simple(req: ScrapeSimpleRequest, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user_id)):
    """Simplified scraper with mode selection."""
    # 支援多組關鍵字
    if req.keywords:
        keywords = req.keywords
    elif req.keyword:
        # 如果是逗號分隔的字串，將其拆分為列表
        keywords = [k.strip() for k in req.keyword.split(',')]
    else:
        keywords = ["manufacturer"]
    
    if req.miner_mode == "manufacturer":
        import manufacturer_miner
        import asyncio
        
        def run_manufacturer_task_sync():
            """同步包裝函式，讓 FastAPI BackgroundTasks 能正確執行 async 任務"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for kw in keywords:
                    loop.run_until_complete(
                        manufacturer_miner.manufacturer_mine(kw, req.market, req.pages, current_user.id)
                    )
            finally:
                loop.close()
        
        background_tasks.add_task(run_manufacturer_task_sync)
        return {"message": f"Manufacturer Mode mining started for {req.market} with {len(keywords)} keywords"}
    else:
        import scrape_simple as scrape_mod
        import asyncio
        
        def run_yellowpages_task_sync():
            """同步包裝函式，讓 FastAPI BackgroundTasks 能正確執行任務"""
            # 即使 scrape_simple 是 sync，但在 FastAPI 背景執行緒中，
            # 若內層有 asyncio.run() 可能會與父執行緒 loop 衝突，故採隔離 loop 模式。
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                scrape_mod.scrape_simple(req.market, req.pages, keywords, current_user.id)
            finally:
                loop.close()
        
        background_tasks.add_task(run_yellowpages_task_sync)
        return {"message": f"Yellowpages Mode mining started for {req.market} with {len(keywords)} keywords"}

@app.get("/api/search-history")
def get_search_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """獲取用戶的所有探勘歷史記錄"""
    tasks = db.query(models.ScrapeTask).filter(
        models.ScrapeTask.user_id == current_user.id
    ).order_by(models.ScrapeTask.id.desc()).all()
    
    return [
        {
            "id": t.id,
            "market": t.market,
            "keywords": t.keywords,
            "miner_mode": t.miner_mode,
            "pages_requested": t.pages_requested,
            "status": t.status,
            "leads_found": t.leads_found,
            "started_at": t.started_at.strftime("%Y-%m-%d %H:%M:%S") if t.started_at else "",
            "completed_at": t.completed_at.strftime("%Y-%m-%d %H:%M:%S") if t.completed_at else ""
        }
        for t in tasks
    ]

# ══════════════════════════════════════════
# AI Keyword Generator
# ══════════════════════════════════════════

class KeywordGenerateRequest(BaseModel):
    keyword: str
    count: int = 5

@app.post("/api/keywords/generate")
def generate_keywords(req: KeywordGenerateRequest, current_user: models.User = Depends(get_current_user_id)):
    """Generate related keywords using AI"""
    try:
        keywords = ai_service.generate_related_keywords(req.keyword, req.count)
        return {"success": True, "keywords": keywords}
    except Exception as e:
        add_log(f"Keyword generation error: {e}", level="error")
        return {"success": False, "message": str(e)}

@app.get("/api/templates")
def get_templates(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    templates = db.query(models.EmailTemplate).filter(
        models.EmailTemplate.user_id == current_user.id
    ).order_by(models.EmailTemplate.tag, models.EmailTemplate.name).all()
    return [t.to_dict() for t in templates]

@app.post("/api/templates", response_model=EmailTemplateResponse)
def create_template(template: EmailTemplateCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    db_template = models.EmailTemplate(
        user_id=current_user.id,
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
    return db_template.to_dict()

# ══════════════════════════════════════════
# Vendor (委外廠商) Admin Endpoints (Admin Only)
# ══════════════════════════════════════════

class VendorCreateReq(BaseModel):
    email: str
    password: str
    company_name: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    pricing_config: Optional[dict] = None

@app.get("/api/admin/vendors")
def list_vendors(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：列出所有委外廠商"""
    vendors = db.query(models.Vendor).all()
    return [v.to_dict() for v in vendors]

@app.post("/api/admin/vendors")
def create_vendor(req: VendorCreateReq, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：建立新委外廠商帳號"""
    import json
    
    # 1. 檢查帳號是否存在
    existing = db.query(models.User).filter(models.User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="此 Email 帳號已存在")
    
    # 2. 建立 User 帳號
    user = models.User(
        email=req.email,
        name=req.contact_name or req.company_name,
        company_name=req.company_name,
        role='vendor'
    )
    user.set_password(req.password)
    db.add(user)
    db.flush() 
    
    # 3. 建立 Vendor 管理資料
    vendor = models.Vendor(
        user_id=user.id,
        company_name=req.company_name,
        contact_name=req.contact_name,
        contact_phone=req.contact_phone,
        pricing_config=json.dumps(req.pricing_config or {})
    )
    db.add(vendor)
    
    # 4. 建立預設訂閱 (Enterprise for Vendors)
    ent_plan = db.query(models.Plan).filter(models.Plan.name == "enterprise").first()
    if ent_plan:
        from datetime import timedelta
        sub = models.Subscription(
            user_id=user.id,
            plan_id=ent_plan.id,
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=365 * 100)
        )
        db.add(sub)
    
    db.commit()
    return vendor.to_dict()

@app.patch("/api/admin/vendors/{vendor_id}")
def update_vendor(vendor_id: int, updates: dict, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：更新廠商資訊"""
    import json
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="找不到該廠商")
        
    for key, value in updates.items():
        if key == "pricing_config" and isinstance(value, dict):
            vendor.pricing_config = json.dumps(value)
        elif hasattr(vendor, key):
            setattr(vendor, key, value)
            
    db.commit()
    return vendor.to_dict()

@app.delete("/api/admin/vendors/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：刪除廠商"""
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="找不到該廠商")
    
    user = vendor.user
    if user:
        user.is_active = False 
        
    db.delete(vendor)
    db.commit()
    return {"message": "廠商已刪除"}

# ══════════════════════════════════════════
# Admin - 會員管理 (Member Management)
# ══════════════════════════════════════════

class MemberUpdateReq(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None  # 'admin', 'vendor', 'member'
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    plan: Optional[str] = None  # 'free', 'pro', 'enterprise'

@app.get("/api/admin/members")
def list_members(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth_module.require_role(["admin"])),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
    """管理員：列出所有會員（支援篩選）"""
    query = db.query(models.User)
    
    if role:
        query = query.filter(models.User.role == role)
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if search:
        query = query.filter(
            (models.User.email.ilike(f"%{search}%")) |
            (models.User.name.ilike(f"%{search}%")) |
            (models.User.company_name.ilike(f"%{search}%"))
        )
    
    users = query.order_by(models.User.created_at.desc()).all()
    
    result = []
    for u in users:
        # 取得訂閱資訊
        sub = db.query(models.Subscription).filter(
            models.Subscription.user_id == u.id,
            models.Subscription.status == 'active'
        ).first()
        
        # 取得本月用量
        usage = UsageLog.get_or_create(db, u.id) if u.role == 'member' else None
        
        result.append({
            **u.to_dict(),
            "subscription": sub.to_dict() if sub else None,
            "usage": usage.to_dict() if usage else None
        })
    
    return result

@app.get("/api/admin/members/{member_id}")
def get_member_detail(member_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：取得會員詳情"""
    user = db.query(models.User).filter(models.User.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該會員")
    
    # 訂閱資訊
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user.id).first()
    
    # 用量統計
    usage = UsageLog.get_or_create(db, user.id)
    
    # Leads 數量
    leads_count = db.query(models.Lead).filter(models.Lead.user_id == user.id).count()
    
    # Email Logs
    emails_sent = db.query(models.EmailLog).filter(models.EmailLog.user_id == user.id).count()
    emails_opened = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == user.id, 
        models.EmailLog.opened == True
    ).count()
    
    return {
        **user.to_dict(include_sensitive=True),
        "subscription": sub.to_dict() if sub else None,
        "usage": usage.to_dict(),
        "stats": {
            "leads_count": leads_count,
            "emails_sent": emails_sent,
            "emails_opened": emails_opened,
            "open_rate": round(emails_opened / emails_sent * 100, 1) if emails_sent > 0 else 0
        }
    }

@app.patch("/api/admin/members/{member_id}")
def update_member(member_id: int, updates: MemberUpdateReq, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：更新會員資訊"""
    user = db.query(models.User).filter(models.User.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該會員")
    
    # 防止管理員把自己降級
    if user.id == current_user.id and updates.role and updates.role != 'admin':
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    
    if updates.name is not None:
        user.name = updates.name
    if updates.role is not None:
        user.role = updates.role
    if updates.is_active is not None:
        user.is_active = updates.is_active
    if updates.is_verified is not None:
        user.is_verified = updates.is_verified
    
    # 調整方案
    if updates.plan is not None and user.role == 'member':
        plan = db.query(models.Plan).filter(models.Plan.name == updates.plan).first()
        if not plan:
            raise HTTPException(status_code=400, detail=f"找不到方案: {updates.plan}")
        
        # 更新或建立 Subscription
        sub = db.query(models.Subscription).filter(models.Subscription.user_id == user.id).first()
        if sub:
            sub.plan_id = plan.id
            sub.status = 'active'
        else:
            sub = models.Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status='active'
            )
            db.add(sub)
    
    db.commit()
    db.refresh(user)
    return user.to_dict()

@app.delete("/api/admin/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：刪除會員（軟刪除）"""
    user = db.query(models.User).filter(models.User.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該會員")
    
    # 防止刪除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能刪除自己的帳號")
    
    # 軟刪除
    user.is_active = False
    db.commit()
    return {"message": "會員已停用", "user_id": member_id}

@app.post("/api/admin/members/{member_id}/reset-password")
def reset_member_password(member_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：重設會員密碼"""
    import secrets
    user = db.query(models.User).filter(models.User.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該會員")
    
    # 產生臨時密碼
    temp_password = secrets.token_urlsafe(12)
    user.set_password(temp_password)
    user.reset_token = secrets.token_urlsafe(32)
    db.commit()
    
    return {
        "message": "密碼已重設",
        "temp_password": temp_password,
        "reset_token": user.reset_token
    }

@app.get("/api/admin/stats")
def get_admin_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：儀表板統計數據"""
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    total_leads = db.query(models.Lead).count()
    total_emails = db.query(models.EmailLog).count()
    
    # 各角色統計
    admins = db.query(models.User).filter(models.User.role == 'admin').count()
    vendors = db.query(models.User).filter(models.User.role == 'vendor').count()
    members = db.query(models.User).filter(models.User.role == 'member').count()
    
    # 本月新增
    from datetime import datetime
    now = datetime.utcnow()
    new_this_month = db.query(models.User).filter(
        models.User.created_at >= datetime(now.year, now.month, 1)
    ).count()
    
    # 方案分佈統計
    free_count = db.query(models.User).join(models.Subscription).join(models.Plan).filter(
        models.Plan.name == 'free'
    ).count()
    pro_count = db.query(models.User).join(models.Subscription).join(models.Plan).filter(
        models.Plan.name == 'pro'
    ).count()
    enterprise_count = db.query(models.User).join(models.Subscription).join(models.Plan).filter(
        models.Plan.name == 'enterprise'
    ).count()
    
    # 探勘任務統計
    total_tasks = db.query(models.ScrapeTask).count()
    active_tasks = db.query(models.ScrapeTask).filter(models.ScrapeTask.status == 'Running').count()
    completed_tasks = db.query(models.ScrapeTask).filter(models.ScrapeTask.status == 'Completed').count()
    
    # 計算開信統計
    emails_opened = db.query(models.EmailLog).filter(models.EmailLog.opened == True).count()
    open_rate = round((emails_opened / total_emails * 100), 1) if total_emails > 0 else 0

    # 提案統計 (v3.0)
    pending_proposals = db.query(models.GlobalProposal).filter(models.GlobalProposal.status == 'Pending').count()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_this_month": new_this_month,
            "by_role": { "admin": admins, "vendor": vendors, "member": members },
            "by_plan": { "free": free_count, "pro": pro_count, "enterprise": enterprise_count }
        },
        "data": {
            "total_leads": total_leads,
            "total_emails_sent": total_emails,
            "total_emails_opened": emails_opened,
            "open_rate": open_rate,
            "pending_proposals": pending_proposals
        },
        "usage": {
            "total_scrape_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks
        }
    }

@app.get("/api/admin/global-pool/stats")
def get_global_pool_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：獲取全域隔離池統計數據 (v2.7.1)"""
    total_leads = db.query(models.GlobalLead).count()
    total_domains = db.query(models.GlobalLead).filter(models.GlobalLead.domain != None).count()
    
    # 產業分布 (依據 ai_tag)
    tag_counts = db.query(
        models.GlobalLead.ai_tag, 
        func.count(models.GlobalLead.id)
    ).group_by(models.GlobalLead.ai_tag).all()
    
    return {
        "total_leads": total_leads,
        "total_domains": total_domains,
        "tags": {tag: count for tag, count in tag_counts if tag}
    }

@app.post("/api/admin/global-pool/clear")
def clear_global_pool(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：清空全域隔離池 (v2.7.1)"""
    db.query(models.GlobalLead).delete()
    db.commit()
    return {"message": "全域隔離池已清空"}
# ══════════════════════════════════════════
# Shared Intelligence: 資料修正提案 (v3.0)
# ══════════════════════════════════════════

class ProposalCreate(BaseModel):
    global_id: int
    field_name: str
    suggested_value: str

@app.post("/api/leads/propose")
def create_proposal(payload: ProposalCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.get_current_user)):
    """提交全域資料修正建議"""
    global_lead = db.query(models.GlobalLead).filter(models.GlobalLead.id == payload.global_id).first()
    if not global_lead:
        raise HTTPException(status_code=404, detail="找不到全域資料")
    
    # 獲取目前值
    current_val = getattr(global_lead, payload.field_name, "")
    if isinstance(current_val, bytes): current_val = current_val.decode('utf-8')
    
    proposal = models.GlobalProposal(
        user_id=current_user.id,
        global_id=payload.global_id,
        field_name=payload.field_name,
        current_value=str(current_val),
        suggested_value=payload.suggested_value,
        status="Pending"
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal.to_dict()

@app.get("/api/admin/proposals")
def list_proposals(status: str = "Pending", db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：查看提案列表"""
    proposals = db.query(models.GlobalProposal).filter(models.GlobalProposal.status == status).order_by(models.GlobalProposal.id.desc()).all()
    return [p.to_dict() for p in proposals]

class ProposalResolve(BaseModel):
    status: str # 'Approved', 'Rejected'
    reason: Optional[str] = None

@app.post("/api/admin/proposals/{proposal_id}/resolve")
def resolve_proposal(proposal_id: int, payload: ProposalResolve, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    """管理員：審核提案"""
    proposal = db.query(models.GlobalProposal).filter(models.GlobalProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="找不到提案")
    
    proposal.status = payload.status
    proposal.reason = payload.reason
    proposal.resolved_at = datetime.utcnow()
    
    if payload.status == "Approved":
        # 套用到全域資料
        global_lead = db.query(models.GlobalLead).filter(models.GlobalLead.id == proposal.global_id).first()
        if global_lead:
            setattr(global_lead, proposal.field_name, proposal.suggested_value)
            global_lead.is_verified = True # 經過審核即視為驗證過
            
    db.commit()
    return {"message": f"提案已 {payload.status}", "proposal_id": proposal_id}

# ══════════════════════════════════════════
# Admin: 爬蟲監控 API
# ══════════════════════════════════════════

@app.get("/api/admin/scrape-tasks")
def list_scrape_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """管理員：查看所有爬蟲任務"""
    query = db.query(models.ScrapeTask)
    if status:
        query = query.filter(models.ScrapeTask.status == status)
    tasks = query.order_by(models.ScrapeTask.id.desc()).limit(limit).all()
    return [t.to_dict(include_logs=False) for t in tasks]

@app.get("/api/admin/scrape-tasks/{task_id}")
def get_scrape_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """管理員：查看爬蟲任務詳情 + 完整日誌"""
    task = db.query(models.ScrapeTask).filter(models.ScrapeTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="找不到該任務")
    return task.to_dict(include_logs=True)

@app.get("/api/admin/scrape-tasks/{task_id}/logs")
def get_scrape_task_logs(
    task_id: int,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """管理員：查看任務日誌"""
    query = db.query(models.ScrapeLog).filter(models.ScrapeLog.task_id == task_id)
    if level:
        query = query.filter(models.ScrapeLog.level == level)
    logs = query.order_by(models.ScrapeLog.id.asc()).all()
    return [log.to_dict() for log in logs]

@app.put("/api/admin/scrape-tasks/{task_id}/retry")
def retry_scrape_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """管理員：重試失敗的爬蟲任務"""
    task = db.query(models.ScrapeTask).filter(models.ScrapeTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="找不到該任務")
    if task.status not in ("Failed", "Completed"):
        raise HTTPException(status_code=400, detail="只能重試失敗或已完成的任務")
    
    # 建立新任務
    keywords = task.keywords.split(",") if task.keywords else ["manufacturer"]
    new_task = models.ScrapeTask(
        user_id=task.user_id,
        market=task.market,
        keywords=task.keywords,
        miner_mode=task.miner_mode,
        pages_requested=task.pages_requested,
        status="Running"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # 標記舊任務
    task.status = f"Retried->#{new_task.id}"
    db.commit()
    
    # 啟動背景任務
    if task.miner_mode == "manufacturer":
        import manufacturer_miner
        import asyncio
        
        def run_retry_manufacturer_task_sync():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for kw in keywords:
                    loop.run_until_complete(
                        manufacturer_miner.manufacturer_mine(kw, task.market, task.pages_requested, task.user_id)
                    )
            finally:
                loop.close()
        
        background_tasks.add_task(run_retry_manufacturer_task_sync)
    else:
        import scrape_simple as scrape_mod
        background_tasks.add_task(scrape_mod.scrape_simple, task.market, task.pages_requested, keywords, task.user_id)
    
    return {"message": f"已建立重試任務 #{new_task.id}", "new_task_id": new_task.id}

@app.delete("/api/admin/scrape-tasks/stale")
def cleanup_stale_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """管理員：清理卡住的 Running 任務（超過 10 分鐘）"""
    from datetime import datetime, timedelta
    threshold = datetime.utcnow() - timedelta(minutes=10)
    
    stale = db.query(models.ScrapeTask).filter(
        models.ScrapeTask.status == "Running",
        models.ScrapeTask.started_at < threshold
    ).all()
    
    count = 0
    for task in stale:
        task.status = "Failed"
        task.error_message = "自動標記為失敗（超時超過 10 分鐘，可能被系統中斷）"
        task.completed_at = datetime.utcnow()
        count += 1
    
    db.commit()
    return {"message": f"已清理 {count} 個卡住的任務", "cleaned": count}

@app.put("/api/templates/{template_id}", response_model=EmailTemplateResponse)
def update_template(template_id: int, template: EmailTemplateCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    db_template = db.query(models.EmailTemplate).filter(
        models.EmailTemplate.id == template_id,
        models.EmailTemplate.user_id == current_user.id
    ).first()
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
    return db_template.to_dict()

@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    db_template = db.query(models.EmailTemplate).filter(
        models.EmailTemplate.id == template_id,
        models.EmailTemplate.user_id == current_user.id
    ).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    add_log(f"✉️ [模板] 刪除模板 ID: {template_id}")
    return {"message": "Template deleted"}

# --- AI Template Generation ---

class AITemplateRequest(BaseModel):
    prompt: str
    style: str = "professional"  # professional, friendly, technical
    language: str = "english"  # english, chinese

@app.post("/api/templates/ai-generate")
def ai_generate_template(req: AITemplateRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """Use AI to generate HTML email template."""
    import openai
    from config_utils import get_api_key, get_openai_model
    
    api_key = get_api_key(db, "openai", current_user.id)
    model = get_openai_model(db, current_user.id)
    
    if not api_key:
        return {"success": False, "html": "", "message": "OpenAI API Key not set in Dashboard"}
    
    openai.api_key = api_key
    
    system_prompt = """你是一個專業的 B2B 商務開發信設計師。
請根據以下需求，產生一封完整的 HTML Email 模板。

要求：
1. 使用 inline CSS（確保 Gmail 相容）
2. 包含 Header（可放公司名稱或 Logo placeholder）
3. 段落清晰，重點用 bold 標示
4. 結尾加上聯絡資訊區塊
5. 保留以下變數佔位符，不要替換掉：
 - {{company_name}}：目標客戶公司名
 - {{bd_name}}：業務負責人姓名
 - {{keywords}}：產品關鍵字
 - {{description}}：公司描述
6. 只輸出純 HTML，從 <!DOCTYPE html> 開始，不要 markdown，不要解釋"""

    style_guide = {
        "professional": "語氣正式、專業，適合大型企業",
        "friendly": "語氣親切、溫溫，適合中小企業",
        "technical": "強調技術細節與規格，適合工程師"
    }
    
    user_prompt = f"""
需求：{req.prompt}
語言：{req.language}
風格：{style_guide.get(req.style, style_guide['professional'])}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000
        )
        
        html = response.choices[0].message.content
        add_log(f"✨ [AI] 生成模板成功")
        
        return {
            "success": True,
            "html": html,
            "message": "AI 生成完成"
        }
    except Exception as e:
        add_log(f"❌ [AI] 生成失敗: {str(e)}")
        return {
            "success": False,
            "html": "",
            "message": str(e)
        }

# --- Send Test Email ---

@app.post("/api/templates/test-send")
def send_test_email(current_user: models.User = Depends(get_current_user_id)):
    """Send a test email to the configured SMTP user."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    if not smtp_user or not smtp_password:
        return {"success": False, "message": "SMTP 尚未設定"}
    
    # Create test email with dummy data
    html_content = """
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>測試信件 - Corelink B2B Engine</h2>
        <p>這是一封測試信件，用於確認模板排版效果。</p>
        <hr>
        <p><strong>公司名稱：</strong>Test Company</p>
        <p><strong>業務代表：</strong>John Doe</p>
        <p><strong>關鍵字：</strong>cable, wire, harness</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Corelink - From Concept to Connect
        </p>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "[測試] Corelink B2B Engine - 模板測試信"
        msg['From'] = smtp_user
        msg['To'] = smtp_user
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        add_log(f"📧 [測試信] 已寄送至 {smtp_user}")
        return {
            "success": True,
            "message": f"測試信已寄送至 {smtp_user}"
        }
    except Exception as e:
        add_log(f"❌ [測試信] 寄送失敗: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

# --- Email Sent Tracking ---
@app.post("/api/leads/{lead_id}/mark-sent", response_model=dict)

# ═══════════════════════════════════════════════════════
# Lead Email Enrichment API - Find email for existing lead
# ═══════════════════════════════════════════════════════

@app.post("/api/leads/{lead_id}/find-email", response_model=dict)
async def find_email_for_lead(
    lead_id: int,
    strategy: str = "free",  # "free" or "hunter"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_id)
):
    """
    Find/Enrich email for an existing lead that doesn't have one.
    """
    # Get lead
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id,
        models.Lead.user_id == current_user.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.email and lead.email.strip():
        return {
            "success": True,
            "message": "Lead already has email",
            "email": lead.email,
            "source": getattr(lead, 'email_source', None) or "existing"
        }
    
    # Try to find email
    from config_utils import get_api_key
    try:
        company_name = lead.company_name or ""
        
        hunter_key = get_api_key(db, "hunter", current_user.id)
        if strategy == "hunter" and hunter_key:
            # Use Hunter.io
            from email_hunter import find_company_emails
            emails = await find_company_emails(company_name, hunter_key)
            if emails:
                lead.email = emails[0]
                lead.email_source = "hunter_io"
                db.commit()
                return {
                    "success": True,
                    "message": "Email found via Hunter.io",
                    "email": lead.email,
                    "source": "hunter_io"
                }
        
        # Use free method
        from free_email_hunter import find_emails_free
        emails = await find_emails_free(company_name)
        
        if emails:
            lead.email = emails[0]
            lead.email_source = "free_auto"
            db.commit()
            return {
                "success": True,
                "message": "Email found via free method",
                "email": lead.email,
                "source": "free_auto"
            }
        
        return {
            "success": False,
            "message": "Could not find email for this company",
            "email": None,
            "source": None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding email: {str(e)}")


@app.post("/api/leads/batch-find-emails", response_model=dict)
async def batch_find_emails(
    lead_ids: List[int],
    strategy: str = "free",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_id)
):
    """
    Batch find emails for multiple leads that don't have emails.
    """
    leads = db.query(models.Lead).filter(
        models.Lead.id.in_(lead_ids),
        models.Lead.user_id == current_user.id,
        models.Lead.email.is_(None)
    ).all()
    
    results = []
    for lead in leads:
        try:
            company_name = lead.company_name or ""
            
            if strategy == "hunter" and os.getenv("HUNTER_API_KEY"):
                from email_hunter import find_company_emails
                emails = await find_company_emails(company_name, os.getenv("HUNTER_API_KEY"))
            else:
                from free_email_hunter import find_emails_free
                emails = await find_emails_free(company_name)
            
            if emails:
                lead.email = emails[0]
                lead.email_source = strategy
                results.append({"lead_id": lead.id, "email": lead.email, "success": True})
            else:
                results.append({"lead_id": lead.id, "email": None, "success": False})
                
        except Exception as e:
            results.append({"lead_id": lead.id, "error": str(e), "success": False})
    
    db.commit()
    
    return {
        "total": len(lead_ids),
        "found": len([r for r in results if r["success"]]),
        "results": results
    }


def mark_email_sent(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id,
        models.Lead.user_id == current_user.id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
    
    lead.email_sent = True
    lead.email_sent_at = datetime.utcnow()
    db.commit()
    
    add_log(f"📧 [寄信] 標記已寄信: {lead.company_name}")
    return {"message": "Email marked as sent"}

# ══════════════════════════════════════════
# Email Tracking Endpoints (No Auth Required)
# ══════════════════════════════════════════

@app.get("/track/open")
async def track_email_open(id: str):
    """Tracking pixel endpoint - no auth required"""
    png_data, content_type, status = email_tracker.handle_open_tracking(id)
    from fastapi.responses import Response
    return Response(content=png_data, media_type=content_type, status_code=status)

@app.get("/track/click")
async def track_email_click(id: str, url: str):
    """Click tracking redirect endpoint - no auth required"""
    redirect_url, status_code = email_tracker.handle_click_tracking(id, url)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url, status_code=status_code)

# ══════════════════════════════════════════
# Email Engagement API (New EmailLog based)
# ══════════════════════════════════════════

@app.get("/api/engagements")
def get_engagements(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user_id)
):
    """取得追蹤資料 (簡化版 - 移除 vendor_id 關係)"""
    # 權限檢查：Admin 看全部，其他看自己
    if current_user.role == 'admin':
        query_logs = db.query(models.EmailLog)
        query_leads = db.query(models.Lead)
    else:
        query_logs = db.query(models.EmailLog).filter(models.EmailLog.user_id == current_user.id)
        query_leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id)
    
    email_logs = query_logs.all()
    leads = query_leads.all()
    
    # 簡化回傳
    return {
        "email_logs": [log.to_dict() for log in email_logs],
        "leads": [lead.to_dict() for lead in leads],
        "total_logs": len(email_logs),
        "total_leads": len(leads)
    }



@app.post("/api/engagements/{log_uuid}/reply")
def mark_email_replied(log_uuid: str, current_user: models.User = Depends(get_current_user_id)):
    """手動標記回覆"""
    email_tracker.mark_email_replied(log_uuid, source="manual")
    return {"message": "Email marked as replied"}

# --- Pricing Config ---
@app.get("/api/pricing")
def get_pricing(current_user: models.User = Depends(get_current_user_id)):
    return models.pricing_config

@app.put("/api/pricing")
def update_pricing(config: PricingConfigUpdate, current_user: models.User = Depends(get_current_user_id)):
    models.pricing_config.update(config.model_dump())
    add_log(f"💰 收費標準已更新: {config.model_dump()}")
    return {"message": "Pricing updated", "config": models.pricing_config}

# --- SMTP Test ---
@app.post("/api/smtp/test")
def test_smtp_connection(
    server: str,
    port: int,
    user: str,
    password: str,
    current_user: models.User = Depends(get_current_user_id)
):
    """Test SMTP connection with provided credentials."""
    import smtplib
    from email.mime.text import MIMEText
    
    try:
        smtp = smtplib.SMTP(server, port, timeout=10)
        smtp.starttls()
        smtp.login(user, password)
        smtp.quit()
        
        add_log(f"✅ SMTP 測試成功: {user}@{server}")
        return {
            "success": True,
            "message": "SMTP connection successful",
            "server": server,
            "user": user
        }
    except smtplib.SMTPAuthenticationError:
        add_log(f"❌ SMTP 認證失敗: {user}@{server}")
        return {
            "success": False,
            "message": "Authentication failed. Check username and password."
        }
    except smtplib.SMTPConnectError as e:
        add_log(f"❌ SMTP 連線失敗: {server}:{port}")
        return {
            "success": False,
            "message": f"Could not connect to {server}:{port}"
        }
    except Exception as e:
        add_log(f"❌ SMTP 測試錯誤: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }
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
def debug_scrape(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    import scrape_simple
    try:
        scrape_simple.scrape_simple("US", 1)
        return {"message": "Scrape completed"}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

# ══════════════════════════════════════════
# System Settings (Variable Mapping, etc.)
# ══════════════════════════════════════════

class SystemSettingUpdate(BaseModel):
    key: str
    value: Any

@app.get("/api/system/settings")
def get_system_settings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """获取用户的所有系统设置"""
    settings = db.query(models.SystemSetting).filter(models.SystemSetting.user_id == current_user.id).all()
    return {s.key: s.to_dict()["value"] for s in settings}

@app.post("/api/system/settings")
def update_system_setting(setting: SystemSettingUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """更新或创建系统设置"""
    import json
    
    # 查找现有设置
    existing = db.query(models.SystemSetting).filter(
        models.SystemSetting.user_id == current_user.id,
        models.SystemSetting.key == setting.key
    ).first()
    
    val_str = json.dumps(setting.value)
    
    if existing:
        existing.value = val_str
    else:
        new_setting = models.SystemSetting(
            user_id=current_user.id,
            key=setting.key,
            value=val_str
        )
        db.add(new_setting)
    
    db.commit()
    return {"success": True, "key": setting.key}

# INIT: Create database tables
@app.post("/api/init-db")
def init_db(current_user: models.User = Depends(get_current_user_id)):
    """Initialize database tables."""
    from database import engine, Base
    import models
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "Database tables created successfully"}
    except Exception as e:
        return {"error": str(e)}

# DEBUG: Count leads
@app.get("/api/debug-leads")
def debug_leads(db: Session = Depends(get_db)):
    try:
        count = db.query(models.Lead).count()
        return {"count": count, "message": "Query successful"}
    except Exception as e:
        return {"error": str(e)}
