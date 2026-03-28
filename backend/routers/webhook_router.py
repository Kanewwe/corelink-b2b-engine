from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from database import get_db
import models
import ai_service
from logger import add_log
from datetime import datetime

router = APIRouter()

@router.post("/webhooks/postmark/inbound")
async def handle_postmark_inbound(
    db: Session = Depends(get_db),
    payload: dict = Body(...)
):
    """
    接收 Postmark Inbound Webhook (v3.7)
    包含：From, To, Subject, TextBody, HtmlBody, MessageID
    """
    try:
        from_email = payload.get("From")
        to_email = payload.get("To") # 這是接收者，應用來匹配用戶
        subject = payload.get("Subject")
        text_body = payload.get("TextBody")
        html_body = payload.get("HtmlBody")
        message_id = payload.get("MessageID")

        if not from_email or not to_email:
            return {"status": "ignored", "reason": "Missing From/To fields"}

        # 1. 根據 To 地址匹配 Linkora 用戶 (EmailChannelSettings)
        # 註：Postmark 傳來的 To 可能包含姓名，如 "Linkora User <user@company.com>"
        import re
        to_addr_match = re.search(r'[\w\.-]+@[\w\.-]+', to_email)
        to_addr_clean = to_addr_match.group(0) if to_addr_match else to_email

        channel_settings = db.query(models.EmailChannelSettings).filter(
            models.EmailChannelSettings.from_email == to_addr_clean
        ).first()

        if not channel_settings:
            add_log(f"⚠️ [Webhook] Unknown Inbound target: {to_addr_clean}")
            return {"status": "ignored", "reason": f"No user mapped to {to_addr_clean}"}

        target_user_id = channel_settings.user_id

        # 2. 嘗試尋找對應的 Lead
        from_addr_match = re.search(r'[\w\.-]+@[\w\.-]+', from_email)
        from_addr_clean = from_addr_match.group(0) if from_addr_match else from_email
        
        lead = db.query(models.Lead).filter(
            models.Lead.user_id == target_user_id,
            models.Lead.email == from_addr_clean
        ).first()

        # 3. 建立 InboundEmail 記錄
        inbound = models.InboundEmail(
            user_id=target_user_id,
            lead_id=lead.id if lead else None,
            message_id=message_id,
            from_email=from_addr_clean,
            from_name=payload.get("FromName"),
            subject=subject,
            body_text=text_body,
            body_html=html_body,
            status="unread"
        )
        db.add(inbound)
        
        # 4. (Optional) 自動觸發 AI 意圖分析
        if text_body:
            try:
                # 這裡不非同步等待，只做初步標記 (Sprint 2 Logic)
                analysis = await ai_service.analyze_reply_intent(text_body, db=db, user_id=target_user_id)
                inbound.reply_intent = analysis.get("intent")
                # 產生 AI 回覆草稿
                draft = await ai_service.generate_reply_draft(text_body, analysis.get("intent"))
                inbound.ai_draft_suggested = draft
            except Exception as ai_e:
                add_log(f"⚠️ [Webhook] AI analysis failed for inbound {message_id}: {ai_e}")

        db.commit()
        add_log(f"✅ [Webhook] Inbound email processed from {from_addr_clean} to User {target_user_id}")
        
        return {"status": "success", "message_id": message_id}

    except Exception as e:
        add_log(f"🚨 [Webhook] Error processing Postmark inbound: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
