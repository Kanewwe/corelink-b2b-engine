"""
Linkora Backend - Email Router (v3.6)
解耦自 main.py，包含所有 Email 相關路由：
  - GET    /api/templates
  - POST   /api/templates
  - PUT    /api/templates/{id}
  - DELETE /api/templates/{id}
  - POST   /api/templates/ai-generate
  - POST   /api/templates/ai-optimize-subject
  - POST   /api/templates/ai-generate-ab
  - POST   /api/templates/test-send
  - GET    /api/settings/smtp
  - POST   /api/settings/smtp
  - POST   /api/smtp/test
  - GET    /api/engagements
  - POST   /api/engagements/{uuid}/reply
  - GET    /api/pricing
  - PUT    /api/pricing
  - POST   /api/analytics/ai-summary
  - POST   /api/analytics/optimal-send-time
  - POST   /api/analytics/reply-intent
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
import os, json, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, Depends, HTTPException, Cookie, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models
import auth as auth_module
import email_tracker
from logger import add_log

router = APIRouter()
TAIPEI_TZ = timezone(timedelta(hours=8))


# ─── Auth Dependency ────────────────────────────────────────────────────────

def get_current_user(request: Request, session_id: str = Cookie(None), db: Session = Depends(get_db)) -> models.User:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.split(" ")[1]
    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    session = auth_module.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期")
    return session.user


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class EmailTemplateCreate(BaseModel):
    name: str
    tag: str
    subject: str
    body: str
    is_default: bool = False
    attachment_url: Optional[str] = None


class SMTPSettingsReq(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_encryption: str = 'tls'
    from_email: Optional[str] = None
    from_name: Optional[str] = None


class EmailChannelSettingsReq(BaseModel):
    provider: str # 'smtp', 'postmark', 'resend'
    # Postmark specific
    api_token: Optional[str] = None
    message_stream: Optional[str] = "outbound"
    # Common identity
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_active: bool = True


class AITemplateRequest(BaseModel):
    prompt: str
    style: str = "professional"
    language: str = "english"


class SubjectOptimizeRequest(BaseModel):
    subject: str
    company_name: str = ""


class ABTestRequest(BaseModel):
    company_name: str
    tag: str = ""
    keywords: list = []


class PricingConfigUpdate(BaseModel):
    base_fee: int
    per_lead: int
    email_open_track: int
    email_click_track: int
    per_lead_usd: float


class SystemSettingUpdate(BaseModel):
    key: str
    value: Any


# ─── Template Routes ─────────────────────────────────────────────────────────

@router.get("/templates")
def get_templates(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    templates = db.query(models.EmailTemplate).filter(
        models.EmailTemplate.user_id == current_user.id
    ).order_by(models.EmailTemplate.tag, models.EmailTemplate.name).all()
    return [t.to_dict() for t in templates]


@router.post("/templates")
def create_template(template: EmailTemplateCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_template = models.EmailTemplate(
        user_id=current_user.id, name=template.name, tag=template.tag,
        subject=template.subject, body=template.body, is_default=template.is_default,
        attachment_url=template.attachment_url
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    add_log(f"✉️ [模板] 新增模板: {template.name} ({template.tag})")
    return db_template.to_dict()


@router.put("/templates/{template_id}")
def update_template(template_id: int, template: EmailTemplateCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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


@router.post("/templates/ai-generate")
def ai_generate_template(req: AITemplateRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import openai
    from config_utils import get_api_key, get_openai_model
    api_key = get_api_key(db, "openai", current_user.id)
    if not api_key:
        return {"success": False, "html": "", "message": "OpenAI API Key not set"}
    openai.api_key = api_key
    model = get_openai_model(db, current_user.id)
    style_guide = {"professional": "語氣正式、專業", "friendly": "語氣親切、溫溫", "technical": "強調技術細節"}
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是 B2B 商務開發信設計師，產生完整 HTML Email 模板（inline CSS，含 {{company_name}}、{{bd_name}}、{{keywords}} 佔位符），只輸出純 HTML。"},
                {"role": "user", "content": f"需求：{req.prompt}\n語言：{req.language}\n風格：{style_guide.get(req.style, style_guide['professional'])}"}
            ],
            max_tokens=2000
        )
        return {"success": True, "html": response.choices[0].message.content, "message": "AI 生成完成"}
    except Exception as e:
        return {"success": False, "html": "", "message": str(e)}


@router.post("/templates/ai-optimize-subject")
async def optimize_subject(req: SubjectOptimizeRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    from billing_service import deduct_points
    if not deduct_points(current_user.id, "ai_intelligence", {"action": "subject_optimize"}):
        raise HTTPException(status_code=402, detail="點數不足，無法優化主旨。")
    result = await ai_service.optimize_email_subject(subject=req.subject, company_name=req.company_name, db=db, user_id=current_user.id)
    return {"success": True, "suggestions": result.get("suggestions", [req.subject])}


@router.post("/templates/ai-generate-ab")
async def generate_ab_versions(req: ABTestRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    from billing_service import deduct_points
    if not deduct_points(current_user.id, "ai_intelligence", {"action": "ab_test"}):
        raise HTTPException(status_code=402, detail="點數不足，無法生成 A/B 版本。")
    result = await ai_service.generate_ab_test_versions(company_name=req.company_name, tag=req.tag, keywords=req.keywords, db=db, user_id=current_user.id)
    return {"success": True, **result}


@router.post("/templates/test-send")
def send_test_email(current_user: models.User = Depends(get_current_user)):
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    if not smtp_user or not smtp_password:
        return {"success": False, "message": "SMTP 尚未設定"}
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "[測試] Corelink B2B Engine - 模板測試信"
        msg['From'] = smtp_user
        msg['To'] = smtp_user
        msg.attach(MIMEText("<h2>測試信件</h2><p>SMTP 設定正常。</p>", 'html'))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        add_log(f"📧 [測試信] 已寄送至 {smtp_user}")
        return {"success": True, "message": f"測試信已寄送至 {smtp_user}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── SMTP Settings ───────────────────────────────────────────────────────────

@router.get("/settings/smtp")
def get_smtp_settings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    smtp = db.query(models.SMTPSettings).filter(models.SMTPSettings.user_id == current_user.id).first()
    return smtp.to_dict() if smtp else None


@router.post("/settings/smtp")
def save_smtp_settings(req: SMTPSettingsReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
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


@router.post("/smtp/test")
def test_smtp_connection(server: str, port: int, user: str, password: str, current_user: models.User = Depends(get_current_user)):
    try:
        smtp = smtplib.SMTP(server, port, timeout=10)
        smtp.starttls()
        smtp.login(user, password)
        smtp.quit()
        add_log(f"✅ SMTP 測試成功: {user}@{server}")
        return {"success": True, "message": "SMTP connection successful"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentication failed."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Email Channel Settings (v3.5 Postmark Integration) ─────────────────────

@router.get("/settings/email-channel")
def get_email_channel_settings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """獲取當前 Email 通道設定 (Postmark/SMTP)"""
    channel = db.query(models.EmailChannelSettings).filter(
        models.EmailChannelSettings.user_id == current_user.id
    ).first()
    return channel.to_dict() if channel else {
        "provider": "smtp", 
        "is_active": True,
        "from_name": "Linkora Pro",
        "message_stream": "outbound"
    }


@router.post("/settings/email-channel")
def save_email_channel_settings(req: EmailChannelSettingsReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """儲存 Email 通道設定"""
    channel = db.query(models.EmailChannelSettings).filter(
        models.EmailChannelSettings.user_id == current_user.id
    ).first()
    
    if not channel:
        channel = models.EmailChannelSettings(user_id=current_user.id)
        db.add(channel)
    
    channel.provider = req.provider
    channel.api_token = req.api_token
    channel.message_stream = req.message_stream or "outbound"
    channel.from_email = req.from_email
    channel.from_name = req.from_name
    channel.is_active = req.is_active
    
    db.commit()
    db.refresh(channel)
    add_log(f"⚙️ [設定] 用戶 {current_user.email} 已更新 Email 通道為 {req.provider}")
    return channel.to_dict()


@router.post("/test/postmark")
def test_postmark_api(api_token: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """測試 Postmark API Token 並回傳伺服器名稱 (Step 1 & 4)"""
    from postmark_service import verify_postmark_token
    success, result = verify_postmark_token(api_token)
    if success:
        add_log(f"✅ Postmark 測試成功: {result} (User: {current_user.email})")
        return {"success": True, "server_name": result}
    else:
        return {"success": False, "message": result}


@router.get("/test/postmark/domain")
def check_postmark_domain(domain: str, api_token: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """檢查網域 DNS 驗證狀態 (Step 3)"""
    from postmark_service import get_domain_verification_status
    status = get_domain_verification_status(api_token, domain)
    if status is None:
        return {"success": False, "message": "未在 Postmark 找到此網域或查詢失敗"}
    return {"success": True, "status": status}


# ─── Engagements ─────────────────────────────────────────────────────────────

@router.get("/engagements")
def get_engagements(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == 'admin':
        email_logs = db.query(models.EmailLog).all()
        leads = db.query(models.Lead).all()
    else:
        email_logs = db.query(models.EmailLog).filter(models.EmailLog.user_id == current_user.id).all()
        leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).all()
    return {
        "email_logs": [log.to_dict() for log in email_logs],
        "leads": [lead.to_dict() for lead in leads],
        "total_logs": len(email_logs),
        "total_leads": len(leads)
    }


@router.post("/engagements/{log_uuid}/reply")
def mark_email_replied(log_uuid: str, current_user: models.User = Depends(get_current_user)):
    email_tracker.mark_email_replied(log_uuid, source="manual")
    return {"message": "Email marked as replied"}


# ─── Pricing ─────────────────────────────────────────────────────────────────

@router.get("/pricing")
def get_pricing(current_user: models.User = Depends(get_current_user)):
    return models.pricing_config


@router.put("/pricing")
def update_pricing(config: PricingConfigUpdate, current_user: models.User = Depends(get_current_user)):
    models.pricing_config.update(config.model_dump())
    add_log(f"💰 收費標準已更新: {config.model_dump()}")
    return {"message": "Pricing updated", "config": models.pricing_config}


# ─── Analytics ───────────────────────────────────────────────────────────────

@router.post("/analytics/ai-summary")
async def generate_analytics_summary(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    now = datetime.now(TAIPEI_TZ)
    month_start = datetime(now.year, now.month, 1, tzinfo=TAIPEI_TZ)
    email_logs = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == current_user.id,
        models.EmailLog.created_at >= month_start
    ).all()
    sent = len(email_logs)
    opened = sum(1 for log in email_logs if log.opened)
    clicked = sum(1 for log in email_logs if log.clicked)
    bounced = sum(1 for log in email_logs if log.bounced)
    stats = {
        "sent": sent, "opened": opened, "clicked": clicked, "bounced": bounced,
        "open_rate": round(opened / sent * 100, 1) if sent > 0 else 0,
        "click_rate": round(clicked / sent * 100, 1) if sent > 0 else 0,
        "bounce_rate": round(bounced / sent * 100, 1) if sent > 0 else 0,
        "replied": 0, "top_tags": []
    }
    result = await ai_service.generate_weekly_report_summary(
        stats=stats, period_start=month_start.strftime("%Y/%m/%d"),
        period_end=now.strftime("%Y/%m/%d"), db=db, user_id=current_user.id
    )
    return {"success": True, **stats, **result}


@router.post("/analytics/optimal-send-time")
async def get_optimal_send_time(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    result = await ai_service.recommend_optimal_send_time(db, current_user.id)
    return {"success": True, **result}


@router.post("/analytics/reply-intent")
async def analyze_reply_intent(req: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    from billing_service import deduct_points
    if not deduct_points(current_user.id, "ai_intelligence", {"action": "reply_intent"}):
        raise HTTPException(status_code=402, detail="點數不足，無法分析意圖。")
    result = await ai_service.analyze_reply_intent(req.get("email_body", ""), db, current_user.id)
    return {"success": True, **result}


# ─── System Settings ─────────────────────────────────────────────────────────

@router.get("/system/settings")
def get_system_settings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    search_ids = list({current_user.id, 1})
    all_settings = {}
    for uid in reversed(search_ids):
        for s in db.query(models.SystemSetting).filter(models.SystemSetting.user_id == uid).all():
            try:
                all_settings[s.key] = json.loads(s.value)
            except:
                continue
    return all_settings


@router.post("/system/settings")
def update_system_setting(setting: SystemSettingUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    existing = db.query(models.SystemSetting).filter(
        models.SystemSetting.user_id == current_user.id,
        models.SystemSetting.key == setting.key
    ).first()
    val_str = json.dumps(setting.value)
    if existing:
        existing.value = val_str
    else:
        db.add(models.SystemSetting(user_id=current_user.id, key=setting.key, value=val_str))
    db.commit()
    return {"success": True, "key": setting.key}
