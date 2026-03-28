"""
Linkora Backend - Admin Router (v3.6)
解耦自 main.py，包含所有管理員相關路由：
  - GET    /api/admin/vendors
  - POST   /api/admin/vendors
  - PATCH  /api/admin/vendors/{id}
  - DELETE /api/admin/vendors/{id}
  - GET    /api/admin/members
  - GET    /api/admin/members/{id}
  - PATCH  /api/admin/members/{id}
  - GET    /api/admin/all-leads
  - GET|POST /api/admin/proposals/*
  - GET    /api/admin/scrape-tasks/*
  - GET    /api/debug
  - GET    /api/debug/check-admin
  - POST   /api/init-db
  - GET    /api/debug-leads
"""
from datetime import datetime, timedelta
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, Cookie, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models
import auth as auth_module
from logger import add_log
import os

router = APIRouter()


# ─── Auth Dependencies ───────────────────────────────────────────────────────

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

class VendorCreateReq(BaseModel):
    email: str
    password: str
    company_name: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    pricing_config: Optional[dict] = None


class MemberUpdateReq(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    plan: Optional[str] = None


class ProposalCreate(BaseModel):
    lead_id: int
    note: Optional[str] = None


class ProposalResolve(BaseModel):
    action: str  # "approve" or "reject"
    note: Optional[str] = None


# ─── Global Lead CRUD Schemas ────────────────────────────────────────────────

class GlobalLeadUpdate(BaseModel):
    company_name: Optional[str] = None
    domain: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry_code: Optional[str] = None
    industry_name: Optional[str] = None
    sub_industry_code: Optional[str] = None
    sub_industry_name: Optional[str] = None
    industry_tags: Optional[str] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    lead_score: Optional[int] = None


class BatchDeletePayload(BaseModel):
    ids: list[int]


# ─── Debug Routes (no admin required) ────────────────────────────────────────

@router.get("/debug")
def debug():
    return {
        "admin_user": os.getenv("ADMIN_USER"),
        "password_set": bool(os.getenv("ADMIN_PASSWORD")),
        "token_set": bool(os.getenv("API_TOKEN")),
        "openai_set": bool(os.getenv("OPENAI_API_KEY")),
        "database_url": os.getenv("DATABASE_URL", "NOT SET"),
    }


@router.get("/debug/check-admin")
def check_admin(db: Session = Depends(get_db)):
    admin = db.query(models.User).filter(models.User.email == "admin@linkora.com").first()
    if admin:
        return {"exists": True, "role": admin.role, "is_active": admin.is_active}
    return {"exists": False, "count": db.query(models.User).count()}


@router.get("/debug-leads")
def debug_leads(db: Session = Depends(get_db)):
    try:
        count = db.query(models.Lead).count()
        return {"count": count, "message": "Query successful"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/init-db")
def init_db_endpoint(current_user: models.User = Depends(get_current_user)):
    from database import engine, Base
    from migrations import run_migrations
    try:
        Base.metadata.create_all(bind=engine)
        run_migrations()  # v3.7.25: 執行 schema migrations
        return {"message": "Database tables created and migrations applied successfully"}
    except Exception as e:
        return {"error": str(e)}


# ─── Vendor Management ────────────────────────────────────────────────────────

@router.get("/admin/vendors")
def list_vendors(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    return [v.to_dict() for v in db.query(models.Vendor).all()]


@router.post("/admin/vendors")
def create_vendor(req: VendorCreateReq, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    existing = db.query(models.User).filter(models.User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="此 Email 帳號已存在")
    user = models.User(email=req.email, name=req.contact_name or req.company_name, company_name=req.company_name, role='vendor')
    user.set_password(req.password)
    db.add(user)
    db.flush()
    vendor = models.Vendor(
        user_id=user.id, company_name=req.company_name,
        contact_name=req.contact_name, contact_phone=req.contact_phone,
        pricing_config=json.dumps(req.pricing_config or {})
    )
    db.add(vendor)
    ent_plan = db.query(models.Plan).filter(models.Plan.name == "enterprise").first()
    if ent_plan:
        db.add(models.Subscription(
            user_id=user.id, plan_id=ent_plan.id, status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=365 * 100)
        ))
    db.commit()
    return vendor.to_dict()


@router.patch("/admin/vendors/{vendor_id}")
def update_vendor(vendor_id: int, updates: dict, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
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


@router.delete("/admin/vendors/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="找不到該廠商")
    if vendor.user:
        vendor.user.is_active = False
    db.delete(vendor)
    db.commit()
    return {"message": "廠商已刪除"}


# ─── Member Management ────────────────────────────────────────────────────────

@router.get("/admin/members")
def list_members(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"])),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
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
        sub = db.query(models.Subscription).filter(
            models.Subscription.user_id == u.id, models.Subscription.status == 'active'
        ).first()
        result.append({**u.to_dict(), "subscription": sub.to_dict() if sub else None})
    return result


@router.get("/admin/members/{member_id}")
def get_member_detail(member_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    user = db.query(models.User).filter(models.User.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該會員")
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user.id).first()
    leads_count = db.query(models.Lead).filter(models.Lead.user_id == user.id).count()
    return {**user.to_dict(), "subscription": sub.to_dict() if sub else None, "leads_count": leads_count}


@router.patch("/admin/members/{member_id}")
def update_member(member_id: int, updates: MemberUpdateReq, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    user = db.query(models.User).filter(models.User.id == member_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該會員")
    for key, value in updates.dict(exclude_unset=True, exclude={"plan"}).items():
        setattr(user, key, value)
    if updates.plan:
        plan = db.query(models.Plan).filter(models.Plan.name == updates.plan).first()
        if plan:
            sub = db.query(models.Subscription).filter(models.Subscription.user_id == user.id).first()
            if sub:
                sub.plan_id = plan.id
            else:
                db.add(models.Subscription(
                    user_id=user.id, plan_id=plan.id, status="active",
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=365 * 100)
                ))
    db.commit()
    return user.to_dict()


# ─── Admin All-Leads ────────────────────────────────────────────────────────

@router.get("/admin/all-leads")
def get_admin_all_leads(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    leads = db.query(models.Lead).order_by(models.Lead.id.desc()).limit(500).all()
    return [l.to_dict() for l in leads]


# ─── Global Pool CRUD (v3.7.29) ─────────────────────────────────────────────

@router.get("/admin/global-leads")
def get_admin_global_leads(
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """取得全域池所有公司資料"""
    leads = db.query(models.GlobalLead).order_by(
        models.GlobalLead.id.desc()
    ).offset(skip).limit(limit).all()
    return [l.to_dict() for l in leads]


@router.patch("/admin/global-leads/{lead_id}")
def update_global_lead(
    lead_id: int,
    payload: GlobalLeadUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """編輯全域池單筆資料"""
    lead = db.query(models.GlobalLead).filter(
        models.GlobalLead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該公司")
    
    # 更新欄位
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    
    add_log(f"Admin {current_user.email} 更新全域池公司: {lead.company_name}")
    return lead.to_dict()


@router.delete("/admin/global-leads/{lead_id}")
def delete_global_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """刪除全域池單筆資料"""
    lead = db.query(models.GlobalLead).filter(
        models.GlobalLead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該公司")
    
    company_name = lead.company_name
    
    # 清除相關私域池的 FK
    db.query(models.Lead).filter(
        models.Lead.global_id == lead_id
    ).update({"global_id": None})
    
    db.delete(lead)
    db.commit()
    
    add_log(f"Admin {current_user.email} 刪除全域池公司: {company_name}")
    return {"message": "已刪除", "company_name": company_name}


@router.post("/admin/global-leads/batch-delete")
def batch_delete_global_leads(
    payload: BatchDeletePayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """批次刪除全域池資料"""
    leads = db.query(models.GlobalLead).filter(
        models.GlobalLead.id.in_(payload.ids)
    ).all()
    
    count = len(leads)
    for lead in leads:
        # 清除相關私域池 FK
        db.query(models.Lead).filter(
            models.Lead.global_id == lead.id
        ).update({"global_id": None})
        db.delete(lead)
    
    db.commit()
    
    add_log(f"Admin {current_user.email} 批次刪除全域池 {count} 筆資料")
    return {"message": f"已刪除 {count} 筆", "count": count}


# ─── User Leads CRUD (v3.7.29) ───────────────────────────────────────────────

@router.patch("/admin/leads/{lead_id}")
def update_user_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """編輯用戶私域池單筆資料"""
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    
    add_log(f"Admin {current_user.email} 更新用戶名單: {lead.company_name}")
    return lead.to_dict()


@router.delete("/admin/leads/{lead_id}")
def delete_user_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """刪除用戶私域池單筆資料"""
    lead = db.query(models.Lead).filter(
        models.Lead.id == lead_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    
    company_name = lead.company_name
    user_email = lead.user.email if lead.user else "Unknown"
    
    db.delete(lead)
    db.commit()
    
    add_log(f"Admin {current_user.email} 刪除用戶 {user_email} 的名單: {company_name}")
    return {"message": "已刪除", "company_name": company_name}


# ─── Proposals ───────────────────────────────────────────────────────────────

@router.post("/leads/propose")
def create_proposal(payload: ProposalCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    lead = db.query(models.Lead).filter(models.Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="找不到該名單")
    proposal = models.Proposal(lead_id=payload.lead_id, user_id=current_user.id, note=payload.note, status="Pending")
    db.add(proposal)
    db.commit()
    return proposal.to_dict()


@router.get("/admin/proposals")
def list_proposals(status: str = "Pending", db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    proposals = db.query(models.Proposal).filter(models.Proposal.status == status).all()
    return [p.to_dict() for p in proposals]


@router.post("/admin/proposals/{proposal_id}/resolve")
def resolve_proposal(proposal_id: int, payload: ProposalResolve, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    proposal = db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="找不到該提案")
    proposal.status = "Approved" if payload.action == "approve" else "Rejected"
    proposal.resolved_note = payload.note
    proposal.resolved_at = datetime.utcnow()
    db.commit()
    return proposal.to_dict()


# ─── Scrape Tasks ─────────────────────────────────────────────────────────────

@router.get("/admin/scrape-tasks")
def list_scrape_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    tasks = db.query(models.ScrapeTask).order_by(models.ScrapeTask.id.desc()).limit(100).all()
    return [t.to_dict() for t in tasks]


@router.get("/admin/scrape-tasks/{task_id}")
def get_scrape_task_detail(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth_module.require_role(["admin"]))):
    task = db.query(models.ScrapeTask).filter(models.ScrapeTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="找不到該任務")
    return task.to_dict()
