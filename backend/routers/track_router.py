"""
Linkora Backend - Tracking Router (v3.6)
解耦自 main.py，無需認證的追蹤 Pixel 路由：
  - GET /track/open
  - GET /track/click
"""
from fastapi import APIRouter
from fastapi.responses import Response, RedirectResponse
import email_tracker

router = APIRouter()


@router.get("/track/open")
async def track_email_open(id: str):
    """Tracking pixel endpoint — no auth required"""
    png_data, content_type, status = email_tracker.handle_open_tracking(id)
    return Response(content=png_data, media_type=content_type, status_code=status)


@router.get("/track/click")
async def track_email_click(id: str, url: str):
    """Click tracking redirect — no auth required"""
    redirect_url, status_code = email_tracker.handle_click_tracking(id, url)
    return RedirectResponse(url=redirect_url, status_code=status_code)
