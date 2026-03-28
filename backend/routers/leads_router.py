"""
Linkora Backend - Leads Router (v3.6)
解耦自 main.py，包含所有 Lead 相關路由：
  - POST   /api/leads
  - GET    /api/leads
  - PATCH  /api/leads/{id}
  - GET    /api/leads/{id}/emails
  - POST   /api/leads/{id}/mark-sent
  - POST   /api/leads/{id}/find-email
  - POST   /api/leads/batch-find-emails
  - GET    /api/campaigns
  - GET    /api/dashboard/stats
  - GET    /api/system-logs
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Cookie, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models
import auth as auth_module
from logger import add_log, SYSTEM_LOGS

router = APIRouter()

# GMT+8
TAIPEI_TZ = timezone(timedelta(hours=8))


# ─── Auth Dependency (shared) ─────────────────────────────────────────────

def get_current_user(request: Request, session_id: str = Cookie(None), db: Session = Depends(get_db)) -> models.User:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.split(" ")[1]
    if not session_id:
        raise HTTPException(status_code=401, detail="請先登入")
    session = auth_module.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session 已過期，請重新登入")
    return session.user


# ─── Pydantic Schemas ────────────────────────────────────────────────────

class LeadCreateReq(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    description: str


class LeadUpdateReq(BaseModel):
    override_name: Optional[str] = None
    override_email: Optional[str] = None
    personal_notes: Optional[str] = None
    custom_tags: Optional[str] = None
    status: Optional[str] = None
    assigned_bd: Optional[str] = None
    industry_taxonomy: Optional[str] = None


class LeadScoreRequest(BaseModel):
    lead_ids: Optional[List[int]] = None


# ─── Routes ─────────────────────────────────────────────────────────────

@router.post("/leads")
def create_and_tag_lead(lead: LeadCreateReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    import email_finder
    import asyncio

    plan = auth_module.get_user_plan(db, current_user.id)
    usage = auth_module.get_user_usage(db, current_user.id)
    if plan.max_customers != -1 and usage.customers_count >= plan.max_customers:
        raise HTTPException(status_code=429, detail={"error": "usage_limit_exceeded", "message": f"客戶數已達上限（{usage.customers_count}/{plan.max_customers}），請升級方案", "upgrade_required": True})

    tag_result = ai_service.analyze_company_and_tag(lead.company_name, lead.description, use_gpt=False)
    keywords_list = tag_result.get("Keywords", [])
    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)
    assigned_bd = tag_result.get("BD") or "General"
    ai_tag = tag_result.get("Tag") or "UNKNOWN"

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
        status="Tagged",
        user_id=current_user.id
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead.to_dict()


@router.get("/leads")
def get_leads(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).order_by(models.Lead.id.desc()).all()
    return [l.to_dict() for l in leads]


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: int, updates: LeadUpdateReq, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    for key, value in updates.dict(exclude_unset=True).items():
        if hasattr(lead, key):
            setattr(lead, key, value)
    db.commit()
    db.refresh(lead)
    return lead.to_dict()


@router.get("/leads/{lead_id}/emails")
def get_emails_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    campaigns = db.query(models.EmailCampaign).filter(
        models.EmailCampaign.lead_id == lead_id,
        models.EmailCampaign.user_id == current_user.id
    ).all()
    return [c.to_dict() for c in campaigns]


@router.post("/leads/{lead_id}/mark-sent")
def mark_email_sent(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    lead.email_sent = True
    lead.status = "Email_Sent"
    db.commit()
    return {"success": True, "id": lead_id}


@router.post("/leads/{lead_id}/find-email")
async def find_email_for_lead(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import email_finder
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    result = await email_finder.find_emails_for_company(lead.company_name)
    if result.get("emails"):
        lead.contact_email = result["emails"][0]
        lead.domain = result.get("domain")
        db.commit()
    return {"success": True, "emails": result.get("emails", []), "domain": result.get("domain")}


@router.post("/leads/batch-find-emails")
async def batch_find_emails(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import email_finder
    leads = db.query(models.Lead).filter(
        models.Lead.user_id == current_user.id,
        models.Lead.contact_email == None
    ).limit(20).all()
    updated = 0
    for lead in leads:
        result = await email_finder.find_emails_for_company(lead.company_name)
        if result.get("emails"):
            lead.contact_email = result["emails"][0]
            lead.domain = result.get("domain")
            updated += 1
    db.commit()
    return {"success": True, "updated": updated, "total": len(leads)}


@router.post("/leads/ai-score")
def score_leads(req: LeadScoreRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    query = db.query(models.Lead).filter(models.Lead.user_id == current_user.id)
    if req.lead_ids:
        query = query.filter(models.Lead.id.in_(req.lead_ids))
    leads = query.all()
    results = []
    for lead in leads:
        score_result = ai_service.score_lead(
            company_name=lead.company_name or "",
            domain=lead.domain or "",
            description=lead.description or "",
            has_email=bool(lead.contact_email),
            has_phone=bool(lead.phone),
            ai_tag=lead.ai_tag or "",
            has_website=bool(lead.website_url),
            user_keywords=lead.extracted_keywords or ""
        )
        lead.ai_score = score_result["score"]
        lead.ai_score_tags = json.dumps(score_result["tags"])
        lead.ai_scored_at = datetime.now(timezone.utc)
        results.append({"id": lead.id, "company_name": lead.company_name, **score_result})
    db.commit()
    return {"success": True, "count": len(results), "results": results}


@router.post("/leads/{lead_id}/ai-brief")
async def generate_lead_brief(lead_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    import ai_service
    from billing_service import deduct_points
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id, models.Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    if not deduct_points(current_user.id, "ai_intelligence", {"lead_id": lead_id}):
        raise HTTPException(status_code=402, detail="點數不足，無法生成 AI 情報。")
    score_result = ai_service.score_lead(
        company_name=lead.company_name or "", domain=lead.domain or "",
        description=lead.description or "", has_email=bool(lead.contact_email),
        has_phone=bool(lead.phone), ai_tag=lead.ai_tag or "",
        has_website=bool(lead.website_url), user_keywords=lead.extracted_keywords or ""
    )
    brief_result = await ai_service.generate_lead_brief(
        company_name=lead.company_name or "", domain=lead.domain or "",
        description=lead.description or "", ai_tag=lead.ai_tag or "", db=db, user_id=current_user.id
    )
    lead.ai_score = score_result["score"]
    lead.ai_score_tags = json.dumps(score_result["tags"])
    lead.ai_brief = brief_result.get("brief", "")
    lead.ai_suggestions = json.dumps(brief_result.get("suggestions", []))
    lead.ai_scored_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "id": lead_id, "company_name": lead.company_name,
            "score": score_result["score"], "tags": score_result["tags"],
            "verdict": score_result["verdict"], "brief": brief_result.get("brief", ""),
            "suggestions": brief_result.get("suggestions", [])}


@router.get("/campaigns")
def get_all_campaign_logs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    campaigns = db.query(models.EmailCampaign).filter(
        models.EmailCampaign.user_id == current_user.id
    ).order_by(models.EmailCampaign.id.desc()).all()
    result = []
    for c in campaigns:
        lead = c.lead
        if lead:
            result.append({
                "id": c.id, "lead_id": c.lead_id, "company_name": lead.company_name,
                "assigned_bd": lead.assigned_bd, "subject": c.subject, "content": c.content,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else ""
            })
    return result


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total_leads = db.query(models.Lead).filter(models.Lead.user_id == current_user.id).count()
    now_taipei = datetime.now(TAIPEI_TZ)
    month_start = datetime(now_taipei.year, now_taipei.month, 1, tzinfo=timezone.utc)
    sent_month = db.query(models.EmailLog).filter(
        models.EmailLog.user_id == current_user.id,
        models.EmailLog.created_at >= month_start
    ).count()
    return {"total_leads": total_leads, "sent_month": sent_month, "open_rate": "0%", "bounce_rate": "0%"}


@router.get("/system-logs")
def get_system_logs(current_user: models.User = Depends(get_current_user)):
    return {"logs": SYSTEM_LOGS}
