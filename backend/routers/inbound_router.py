from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import auth
from logger import add_log

router = APIRouter()

@router.get("/inbound")
def get_inbound_emails(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """取得用戶收到的回信列表 (Sprint 3.3)"""
    query = db.query(models.InboundEmail).filter(
        models.InboundEmail.user_id == current_user.id
    )
    
    if status:
        query = query.filter(models.InboundEmail.status == status)
        
    emails = query.order_by(models.InboundEmail.created_at.desc()).limit(limit).all()
    return [e.to_dict() for e in emails]

@router.get("/inbound/{email_id}")
def get_inbound_detail(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """取得回信詳情與 AI 草稿"""
    email = db.query(models.InboundEmail).filter(
        models.InboundEmail.id == email_id,
        models.InboundEmail.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    # 標記為已讀
    if email.status == "unread":
        email.status = "read"
        db.commit()
        
    return email.to_dict()

@router.post("/inbound/{email_id}/archive")
def archive_inbound_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """將郵件存檔"""
    email = db.query(models.InboundEmail).filter(
        models.InboundEmail.id == email_id,
        models.InboundEmail.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    email.status = "archived"
    db.commit()
    return {"success": True}
