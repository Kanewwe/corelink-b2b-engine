"""
Linkora Backend - Scraper Router (v3.6)
解耦自 main.py，包含所有探勘相關路由：
  - POST /api/scrape
  - POST /api/scrape-simple
  - GET  /api/search-history
  - POST /api/keywords/generate
  - GET  /api/scheduler/status
  - POST /api/scheduler/start
  - POST /api/scheduler/stop
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Cookie, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models
import auth as auth_module
from logger import add_log

router = APIRouter()


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

class ScrapeRequest(BaseModel):
    market: str
    keyword: str


class ScrapeSimpleRequest(BaseModel):
    market: str = "US"
    pages: int = 3
    keywords: Optional[List[str]] = None
    keyword: Optional[str] = None
    location: Optional[str] = None
    email_strategy: str = "free"
    miner_mode: str = "yellowpages"


class KeywordGenerateRequest(BaseModel):
    keyword: str
    count: int = 5


# ─── Routes ─────────────────────────────────────────────────────────────────

@router.post("/scrape")
def trigger_scraper(req: ScrapeRequest, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user)):
    import scraper
    background_tasks.add_task(scraper.scrape_and_process_task, req.market, req.keyword)
    return {"message": f"Scraping task for {req.market} {req.keyword} started."}


@router.post("/scrape-simple")
def trigger_scrape_simple(
    req: ScrapeSimpleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Simplified scraper with Tiered Retrieval (v3.1)"""
    from scrape_utils import sync_leads_from_pool_by_keyword
    try:
        if req.keywords:
            keywords = req.keywords
        elif req.keyword:
            keywords = [k.strip() for k in req.keyword.split(',')]
        else:
            keywords = ["manufacturer"]

        keywords = [k for k in keywords if k.strip()] or ["manufacturer"]

        target_total = req.pages * 10
        total_found_in_intel = 0
        synced_from_pool = 0

        for kw in keywords:
            existing_count = db.query(models.Lead).filter(
                models.Lead.user_id == current_user.id,
                (models.Lead.company_name.ilike(f"%{kw}%")) | (models.Lead.extracted_keywords.ilike(f"%{kw}%"))
            ).count()
            rem_for_kw = max(0, target_total - existing_count)
            if rem_for_kw > 0:
                synced = sync_leads_from_pool_by_keyword(db, current_user.id, kw, limit=rem_for_kw)
                synced_from_pool += synced
                total_found_in_intel += (existing_count + synced)
            else:
                total_found_in_intel += existing_count

        if total_found_in_intel >= target_total:
            return {
                "success": True,
                "message": f"💡 情報庫已有充足資料（共 {total_found_in_intel} 筆），已立即恢復至您的工作區，無需重新探勘。",
                "found_in_intel": total_found_in_intel,
                "synced_from_pool": synced_from_pool,
                "scraper_started": False
            }

        rem_target = target_total - total_found_in_intel
        adj_pages = max(1, (rem_target + 9) // 10)

        from billing_service import deduct_points
        if not deduct_points(current_user.id, "scrape", {"keyword": keywords[0], "pages": adj_pages}):
            raise HTTPException(status_code=402, detail="點數不足，請儲值後再進行探勘。")

        if req.miner_mode == "manufacturer":
            import manufacturer_miner
            import asyncio

            def run_manufacturer_task_sync():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    for kw in keywords:
                        loop.run_until_complete(
                            manufacturer_miner.manufacturer_mine(kw, req.market, adj_pages, current_user.id, req.email_strategy)
                        )
                finally:
                    loop.close()

            background_tasks.add_task(run_manufacturer_task_sync)
            scrape_msg = f"已啟動製造商模式，預計探勘剩餘 {rem_target} 筆名單。"
        else:
            import scrape_simple as scrape_mod
            import asyncio

            def run_yellowpages_task_sync():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    scrape_mod.scrape_simple(req.market, adj_pages, keywords, current_user.id, req.email_strategy)
                finally:
                    loop.close()

            background_tasks.add_task(run_yellowpages_task_sync)
            scrape_msg = f"已啟動黃頁模式，預計探勘剩餘 {rem_target} 筆名單。"

        return {
            "success": True,
            "message": f"✅ 已從情報庫恢復 {total_found_in_intel} 筆資料。{scrape_msg}",
            "found_in_intel": total_found_in_intel,
            "synced_from_pool": synced_from_pool,
            "scraper_started": True,
            "remaining_target": rem_target
        }
    except Exception as e:
        add_log(f"🚨 [ScrapeError] {str(e)}")
        raise HTTPException(status_code=500, detail=f"啟動探勘引擎失敗: {str(e)}")


@router.get("/search-history")
def get_search_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tasks = db.query(models.ScrapeTask).filter(
        models.ScrapeTask.user_id == current_user.id
    ).order_by(models.ScrapeTask.id.desc()).all()
    return [
        {
            "id": t.id, "market": t.market, "keywords": t.keywords,
            "miner_mode": t.miner_mode, "pages_requested": t.pages_requested,
            "status": t.status, "leads_found": t.leads_found,
            "started_at": t.started_at.isoformat() if t.started_at else "",
            "completed_at": t.completed_at.isoformat() if t.completed_at else ""
        }
        for t in tasks
    ]


@router.post("/keywords/generate")
def generate_keywords(req: KeywordGenerateRequest, current_user: models.User = Depends(get_current_user)):
    import ai_service
    try:
        keywords = ai_service.generate_related_keywords(req.keyword, req.count)
        return {"success": True, "keywords": keywords}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/scheduler/start")
def start_scheduler(current_user: models.User = Depends(get_current_user)):
    import email_sender_job
    email_sender_job.start_scheduler()
    return {"message": "Scheduler started", "status": email_sender_job.get_scheduler_status()}


@router.post("/scheduler/stop")
def stop_scheduler(current_user: models.User = Depends(get_current_user)):
    import email_sender_job
    stopped = email_sender_job.stop_scheduler()
    return {"message": "Scheduler stopped" if stopped else "Scheduler was not running",
            "status": email_sender_job.get_scheduler_status()}


@router.get("/scheduler/status")
def get_scheduler_status(current_user: models.User = Depends(get_current_user)):
    import email_sender_job
    return email_sender_job.get_scheduler_status()
