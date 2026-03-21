import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import models
from database import SessionLocal
from logger import add_log

load_dotenv()

SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Default: scheduler is DISABLED
EMAIL_SCHEDULER_ENABLED = os.getenv("EMAIL_SCHEDULER_ENABLED", "false").lower() in ("true", "1", "yes")

scheduler = BackgroundScheduler()

def send_email_job():
    """
    Background job: scan Draft emails and send via SMTP.
    Runs every 2 minutes.
    """
    db = SessionLocal()
    try:
        # Find all Draft emails
        drafts = db.query(models.EmailCampaign).filter(
            models.EmailCampaign.status == "Draft"
        ).limit(5).all()  # Send max 5 per batch
        
        if not drafts:
            return
        
        add_log(f"📬 [排程] 發現 {len(drafts)} 封待發送信件")
        
        for campaign in drafts:
            lead = campaign.lead
            if not lead:
                continue
            
            # Skip if no valid email
            if not lead.email_candidates:
                add_log(f"⚠️ [發信] {lead.company_name} 無有效 Email 候選，跳過")
                campaign.status = "No_Email"
                db.commit()
                continue
            
            # Get first email candidate
            to_email = lead.email_candidates.split(",")[0].strip()
            
            try:
                if SMTP_USER and SMTP_PASSWORD:
                    msg = MIMEMultipart()
                    msg['From'] = SMTP_USER
                    msg['To'] = to_email
                    msg['Subject'] = campaign.subject
                    msg.attach(MIMEText(campaign.content, 'plain'))

                    # Attach file if template has attachment_url
                    template = db.query(models.EmailTemplate).filter(
                        models.EmailTemplate.is_default == True
                    ).first()
                    attachment_url = template.attachment_url if template and template.attachment_url else None
                    if attachment_url:
                        import requests as _requests
                        try:
                            resp = _requests.get(attachment_url, timeout=10)
                            resp.raise_for_status()
                            filename = attachment_url.split('/')[-1].split('?')[0]
                            part = MIMEApplication(resp.content, Name=filename)
                            part['Content-Disposition'] = f'attachment; filename="{filename}"'
                            msg.attach(part)
                            add_log(f"📎 [附件] 已夾帶: {filename}")
                        except Exception as attach_err:
                            add_log(f"⚠️ [附件] 夾帶失敗: {attach_err}")

                    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                        server.starttls()
                        server.login(SMTP_USER, SMTP_PASSWORD)
                        server.send_message(msg)
                    
                    campaign.status = "Sent"
                    lead.status = "Email_Sent"
                    add_log(f"✅ [發信] 成功寄送至 {to_email} ({lead.company_name})")
                else:
                    # No SMTP configured, mark as ready
                    campaign.status = "Ready_To_Send"
                    add_log(f"📋 [發信] {lead.company_name} 信件已準備好，但未設定 SMTP")
                
                db.commit()
                
            except Exception as e:
                add_log(f"❌ [發信] 發送失敗 ({lead.company_name}): {str(e)}")
                campaign.status = "Send_Failed"
                db.commit()
                
    except Exception as e:
        add_log(f"❌ [排程] 發信任務錯誤: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler (only if EMAIL_SCHEDULER_ENABLED is true)."""
    if not EMAIL_SCHEDULER_ENABLED:
        add_log("⏸ [排程] 排程器未啟用 (EMAIL_SCHEDULER_ENABLED=false)")
        return
    if scheduler.running:
        add_log("⏰ [排程] 排程器已在運行中")
        return
    scheduler.add_job(send_email_job, 'interval', minutes=2, id='email_sender')
    scheduler.start()
    add_log("⏰ [排程] 信件發送排程器已啟動 (每 2 分鐘)")

def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        add_log("⏹ [排程] 信件發送排程器已停止")
        return True
    return False

def get_scheduler_status():
    """Return scheduler status."""
    return {
        "running": scheduler.running,
        "enabled": EMAIL_SCHEDULER_ENABLED,
        "jobs": [job.id for job in scheduler.get_jobs()]
    }
