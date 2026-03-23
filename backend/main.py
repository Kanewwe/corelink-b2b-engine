from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Cookie, Response
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
import email_tracker
import auth as auth_module
from contextlib import asynccontextmanager
import email_sender_job
from logger import add_log, SYSTEM_LOGS

# Create database tables automatically
Base.metadata.create_all(bind=engine)

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set tracking base URL
    base_url = os.getenv("APP_BASE_URL", "https://linkoratw.com")
    email_tracker.set_track_base_url(base_url)
    
    # Initialize default plans
    init_default_plans()
    
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
    ai_tag: Optional[str] = None
    assigned_bd: Optional[str] = None
    extracted_keywords: Optional[str] = None
    status: str
    # NEW: Contact info
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    contact_email: Optional[str] = None
    # NEW: Company details
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    categories: Optional[str] = None
    source_domain: Optional[str] = None
    # Email tracking
    email_sent: bool = False
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
    
    return {
        "message": "註冊成功",
        "session_id": session.id,
        "user": auth_module.get_user_full_info(db, user)
    }

@app.post("/api/auth/login")
def auth_login(req: AuthLoginReq, request: Request, response: Response, db: Session = Depends(get_db)):
    """用戶登入"""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    
    if not user or not user.check_password(req.password):
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
    
    return {
        "message": "登入成功",
        "session_id": session.id,
        "user": auth_module.get_user_full_info(db, user)
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

# --- API Endpoints (Session Auth) ---
def get_current_user_id(session_id: str = Cookie(None), db: Session = Depends(get_db)) -> models.User:
    """取得當前用戶（Session 驗證）"""
    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    session = auth_module.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期，請重新登入")
    return session.user

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
    return db_lead

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
    
    return campaign

@app.get("/api/leads/{lead_id}/emails", response_model=List[EmailCampaignResponse])
def get_emails_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    return db.query(models.EmailCampaign).filter(
        models.EmailCampaign.lead_id == lead_id,
        models.EmailCampaign.user_id == current_user.id
    ).all()

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

@app.post("/api/scrape-simple")
def trigger_scrape_simple(req: ScrapeSimpleRequest, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user_id)):
    """Simplified scraper using Yahoo search dorking + email finder."""
    import scrape_simple as scrape_mod
    
    # 支援多組關鍵字
    keywords = req.keywords if req.keywords else ([req.keyword] if req.keyword else ["manufacturer"])
    
    background_tasks.add_task(scrape_mod.scrape_simple, req.market, req.pages, keywords, current_user.id)
    return {"message": f"Scraping started for {req.market} with {len(keywords)} keywords"}

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
    return templates

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
    return db_template

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
    return db_template

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
def ai_generate_template(req: AITemplateRequest, current_user: models.User = Depends(get_current_user_id)):
    """Use AI to generate HTML email template."""
    import openai
    
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
        "friendly": "語氣親切、溫暖，適合中小企業",
        "technical": "強調技術細節與規格，適合工程師"
    }
    
    user_prompt = f"""
需求：{req.prompt}
語言：{req.language}
風格：{style_guide.get(req.style, style_guide['professional'])}
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
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
@app.post("/api/leads/{lead_id}/mark-sent")
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
def get_engagements(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_id)):
    """取得所有追蹤資料，含標籤維度的統計"""
    
    # Get all email logs with related data
    email_logs = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == current_user.id
    ).all()
    leads = db.query(models.Lead).filter(
        models.Lead.user_id == current_user.id
    ).all()
    lead_map = {l.id: l for l in leads}
    
    # Build tag stats
    tag_stats = {}
    for log in email_logs:
        lead = lead_map.get(log.lead_id)
        tag = lead.ai_tag if lead and lead.ai_tag else "UNKNOWN"
        
        if tag not in tag_stats:
            tag_stats[tag] = {"total": 0, "delivered": 0, "opened": 0, "clicked": 0, "replied": 0}
        
        tag_stats[tag]["total"] += 1
        if log.status == "delivered":
            tag_stats[tag]["delivered"] += 1
        if log.opened:
            tag_stats[tag]["opened"] += 1
        if log.clicked:
            tag_stats[tag]["clicked"] += 1
        if log.replied:
            tag_stats[tag]["replied"] += 1
    
    # Build records
    records = []
    for log in email_logs:
        lead = lead_map.get(log.lead_id)
        records.append({
            "id": log.id,
            "log_uuid": log.log_uuid,
            "company_name": lead.company_name if lead else "N/A",
            "ai_tag": lead.ai_tag if lead else "UNKNOWN",
            "recipient": log.recipient,
            "subject": log.subject,
            "status": log.status,
            "sent_at": log.sent_at.strftime("%Y-%m-%d %H:%M") if log.sent_at else "",
            "opened": log.opened,
            "clicked": log.clicked,
            "replied": log.replied
        })
    
    return {
        "records": records,
        "tag_stats": tag_stats,
        "stats": email_tracker.get_engagement_stats(),
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
