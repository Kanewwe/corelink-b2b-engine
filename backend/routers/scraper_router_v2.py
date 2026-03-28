"""
Scraper Router - Extended with Hunter.io (v3.7.30)
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
import models
import auth as auth_module
from logger import add_log
from hunter_scraper import HunterScraper, infer_industry
import os

router = APIRouter()


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class HunterSearchRequest(BaseModel):
    domain: str
    limit: int = 10
    seniority: Optional[str] = None
    department: Optional[str] = None


class EmailFinderRequest(BaseModel):
    first_name: str
    last_name: str
    domain: str


class EmailVerifyRequest(BaseModel):
    email: str


class SaveLeadsRequest(BaseModel):
    leads: List[dict]
    source: str = "hunter"
    source_mode: str = "manufacturer"


# ─── Auth Dependency ──────────────────────────────────────────────────────────

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


# ─── Hunter.io API ────────────────────────────────────────────────────────────

@router.post("/scrape/hunter/domain")
def hunter_domain_search(
    req: HunterSearchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Search emails by domain using Hunter.io
    
    - domain: Company domain (e.g., "company.com")
    - limit: Max results (default 10)
    - seniority: Filter by seniority (junior, senior, executive)
    - department: Filter by department
    """
    # 檢查用戶配額
    if current_user.role == "member":
        usage = auth_module.get_user_usage(db, current_user.id)
        if usage.get("leads_used", 0) >= usage.get("leads_limit", 100):
            raise HTTPException(status_code=403, detail="配額已用完")
    
    # 呼叫 Hunter API
    scraper = HunterScraper()
    result = scraper.domain_search(
        domain=req.domain,
        limit=req.limit,
        seniority=req.seniority,
        department=req.department
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "搜尋失敗"))
    
    return {
        "success": True,
        "domain": req.domain,
        "total": result["total"],
        "emails": result["emails"],
        "source": "hunter"
    }


@router.post("/scrape/hunter/finder")
def hunter_email_finder(
    req: EmailFinderRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Find specific person's email using Hunter.io
    
    - first_name: Person's first name
    - last_name: Person's last name
    - domain: Company domain
    """
    scraper = HunterScraper()
    result = scraper.email_finder(
        first_name=req.first_name,
        last_name=req.last_name,
        domain=req.domain
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "搜尋失敗"))
    
    return result


@router.post("/scrape/hunter/verify")
def hunter_email_verify(
    req: EmailVerifyRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Verify email deliverability using Hunter.io
    
    - email: Email address to verify
    """
    scraper = HunterScraper()
    result = scraper.email_verifier(req.email)
    
    return result


@router.get("/scrape/hunter/account")
def hunter_account_info(
    current_user: models.User = Depends(auth_module.require_role(["admin"]))
):
    """
    Get Hunter.io account info (Admin only)
    """
    scraper = HunterScraper()
    return scraper.get_account_info()


# ─── Save to Global Pool ──────────────────────────────────────────────────────

@router.post("/scrape/save-to-global")
def save_leads_to_global(
    req: SaveLeadsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Save scraped leads to global pool
    
    - leads: List of lead objects
    - source: "hunter"|"apollo"|"google_maps"
    - source_mode: "general"|"manufacturer"|"sales"|"marketing"
    """
    saved = 0
    updated = 0
    skipped = 0
    
    for lead_data in req.leads:
        domain = lead_data.get("domain")
        if not domain:
            skipped += 1
            continue
        
        # 檢查全域庫是否已有
        existing = db.query(models.GlobalLead).filter(
            models.GlobalLead.domain == domain
        ).first()
        
        if existing:
            # 更新現有資料（如果 Email 品質更好）
            new_confidence = lead_data.get("email_confidence", 0)
            if new_confidence > existing.email_confidence:
                existing.contact_email = lead_data.get("contact_email") or existing.contact_email
                existing.email_confidence = new_confidence
                existing.email_verified = lead_data.get("email_verified", False)
                existing.email_source = req.source
                existing.source_mode = req.source_mode
                existing.sync_count += 1
                updated += 1
            else:
                skipped += 1
        else:
            # 新增到全域庫
            # 推斷行業
            industry = infer_industry(
                lead_data.get("company_name", ""),
                lead_data.get("description", "")
            )
            
            new_lead = models.GlobalLead(
                company_name=lead_data.get("company_name"),
                domain=domain,
                website_url=lead_data.get("website_url"),
                description=lead_data.get("description"),
                contact_email=lead_data.get("contact_email"),
                email_candidates=lead_data.get("email_candidates"),
                phone=lead_data.get("phone"),
                address=lead_data.get("address"),
                industry_code=industry["industry_code"],
                industry_name=industry["industry_name"],
                industry_tags=industry["industry_tags"],
                employee_count=lead_data.get("employee_count"),
                email_verified=lead_data.get("email_verified", False),
                email_confidence=lead_data.get("email_confidence", 0),
                email_source=req.source,
                source=req.source,
                source_mode=req.source_mode
            )
            db.add(new_lead)
            saved += 1
    
    db.commit()
    
    add_log(f"Global Pool: {current_user.email} saved {saved}, updated {updated}, skipped {skipped}")
    
    return {
        "success": True,
        "saved": saved,
        "updated": updated,
        "skipped": skipped,
        "total": len(req.leads)
    }


# ─── Sync to Private Pool ─────────────────────────────────────────────────────

@router.post("/scrape/sync-to-private")
def sync_global_to_private(
    global_ids: List[int],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Sync leads from global pool to user's private pool
    
    - global_ids: List of global_lead IDs to sync
    """
    synced = 0
    skipped = 0
    
    for gid in global_ids:
        global_lead = db.query(models.GlobalLead).filter(
            models.GlobalLead.id == gid
        ).first()
        
        if not global_lead:
            skipped += 1
            continue
        
        # 檢查用戶私域池是否已有
        existing = db.query(models.Lead).filter(
            models.Lead.user_id == current_user.id,
            models.Lead.domain == global_lead.domain
        ).first()
        
        if existing:
            skipped += 1
            continue
        
        # 檢查配額
        if current_user.role == "member":
            usage = auth_module.get_user_usage(db, current_user.id)
            if usage.get("leads_used", 0) + synced >= usage.get("leads_limit", 100):
                break
        
        # 同步到私域池
        new_lead = models.Lead(
            user_id=current_user.id,
            global_id=global_lead.id,
            company_name=global_lead.company_name,
            domain=global_lead.domain,
            website_url=global_lead.website_url,
            description=global_lead.description,
            contact_email=global_lead.contact_email,
            email_candidates=global_lead.email_candidates,
            phone=global_lead.phone,
            address=global_lead.address,
            industry_code=global_lead.industry_code,
            industry_name=global_lead.industry_name,
            sub_industry_code=global_lead.sub_industry_code,
            sub_industry_name=global_lead.sub_industry_name,
            industry_tags=global_lead.industry_tags,
            employee_count=global_lead.employee_count,
            email_verified=global_lead.email_verified,
            email_confidence=global_lead.email_confidence,
            source=global_lead.source,
            source_mode=global_lead.source_mode,
            status="new"
        )
        db.add(new_lead)
        
        # 更新全域庫統計
        global_lead.sync_count += 1
        global_lead.last_synced_at = datetime.utcnow()
        
        synced += 1
    
    db.commit()
    
    add_log(f"Private Pool: {current_user.email} synced {synced} leads from global")
    
    return {
        "success": True,
        "synced": synced,
        "skipped": skipped
    }
