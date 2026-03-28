from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import Optional, List

from database import get_db
import auth
import models
from logger import add_log

router = APIRouter()

@router.get("/analytics/delivery-stats")
def get_delivery_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    實時投遞成效數據聚合 (Sprint 3.5)
    Returns: Funnel stats and Daily trends
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # 1. 基礎漏斗數據 (Funnel)
    stats = db.query(
        func.count(models.EmailLog.id).label("sent"),
        func.sum(case((models.EmailLog.opened == True, 1), else_=0)).label("opened"),
        func.sum(case((models.EmailLog.clicked == True, 1), else_=0)).label("clicked"),
        func.sum(case((models.EmailLog.replied == True, 1), else_=0)).label("replied")
    ).filter(
        models.EmailLog.user_id == current_user.id,
        models.EmailLog.sent_at >= cutoff
    ).first()

    sent = stats.sent or 0
    opened = int(stats.opened or 0)
    clicked = int(stats.clicked or 0)
    replied = int(stats.replied or 0)

    # 2. 每日趨勢 (Daily Trends)
    # 這裡使用 func.dateTrunc 或格式化日期
    trends_query = db.query(
        func.date(models.EmailLog.sent_at).label("date"),
        func.count(models.EmailLog.id).label("sent"),
        func.sum(case((models.EmailLog.opened == True, 1), else_=0)).label("opened")
    ).filter(
        models.EmailLog.user_id == current_user.id,
        models.EmailLog.sent_at >= cutoff
    ).group_by(func.date(models.EmailLog.sent_at)).order_by("date").all()

    trends = [{
        "date": str(row.date),
        "sent": row.sent,
        "opened": int(row.opened or 0)
    } for row in trends_query]

    return {
        "period_days": days,
        "funnel": {
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "replied": replied,
            "open_rate": round(opened / sent * 100, 2) if sent > 0 else 0,
            "click_rate": round(clicked / sent * 100, 2) if sent > 0 else 0,
            "reply_rate": round(replied / sent * 100, 2) if sent > 0 else 0
        },
        "trends": trends
    }

@router.get("/analytics/tag-funnel")
def get_tag_funnel_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    依行業標籤 (AI Tag) 劃分的轉化率分析
    """
    # Join EmailLog with Lead to get tags
    results = db.query(
        models.Lead.ai_tag,
        func.count(models.EmailLog.id).label("sent"),
        func.sum(case((models.EmailLog.opened == True, 1), else_=0)).label("opened"),
        func.sum(case((models.EmailLog.clicked == True, 1), else_=0)).label("clicked")
    ).join(
        models.EmailLog, models.Lead.id == models.EmailLog.lead_id
    ).filter(
        models.EmailLog.user_id == current_user.id
    ).group_by(models.Lead.ai_tag).all()

    tag_stats = {}
    for row in results:
        tag = row.ai_tag or "未分類"
        tag_stats[tag] = {
            "sent": row.sent,
            "opened": int(row.opened or 0),
            "clicked": int(row.clicked or 0),
            "open_rate": round(int(row.opened or 0) / row.sent * 100, 2) if row.sent > 0 else 0
        }
    
    return tag_stats
