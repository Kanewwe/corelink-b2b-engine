from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
import auth
import ai_service
import models
from logger import add_log

router = APIRouter()

# --- Request Schemas ---

class IntentAnalysisReq(BaseModel):
    email_body: str
    log_id: Optional[int] = None

class SendTimeRecommendResponse(BaseModel):
    best_day: str
    best_hour: int
    best_time_display: str
    confidence: str
    reason: str

# --- Endpoints ---

@router.post("/ai/classify-intent")
async def classify_reply_intent(
    req: IntentAnalysisReq,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    分析回信意圖 (Sprint 2)
    可傳入 log_id 以便將分析結果存回資料庫
    """
    add_log(f"🤖 [AI] Analyzing intent for user {current_user.email}")
    
    result = await ai_service.analyze_reply_intent(req.email_body, db=db, user_id=current_user.id)
    
    # 如果提供 log_id，則存回資料庫
    if req.log_id:
        email_log = db.query(models.EmailLog).filter(
            models.EmailLog.id == req.log_id,
            models.EmailLog.user_id == current_user.id
        ).first()
        
        if email_log:
            email_log.reply_intent = result.get("intent")
            email_log.reply_analysis = result.get("analysis")
            email_log.reply_next_action = result.get("next_action")
            db.commit()
            add_log(f"✅ [AI] Intent stored for EmailLog {req.log_id}")

    return result

@router.get("/ai/recommend-send-time", response_model=SendTimeRecommendResponse)
async def get_send_time_recommendation(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    取得最佳寄信時間建議 (Sprint 2)
    """
    add_log(f"🤖 [AI] Recommending send time for user {current_user.email}")
    return await ai_service.recommend_optimal_send_time(db, current_user.id)

@router.get("/ai/stats-insight")
async def get_ai_stats_insight(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    額外功能：AI 儀表板深入洞察
    """
    # 這裡可以實作從 EmailLog 總結 intent 分佈的邏輯
    from sqlalchemy import func
    
    stats = db.query(
        models.EmailLog.reply_intent, 
        func.count(models.EmailLog.id)
    ).filter(
        models.EmailLog.user_id == current_user.id,
        models.EmailLog.reply_intent.isnot(None)
    ).group_by(models.EmailLog.reply_intent).all()
    
    return {
        "intent_distribution": {row[0]: row[1] for row in stats},
        "message": "AI 洞察分析由 Sprint 2 提供支持"
    }
