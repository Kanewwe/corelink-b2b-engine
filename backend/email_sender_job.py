import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import models
import email_tracker
from database import SessionLocal
from logger import add_log
from billing_service import deduct_points

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
    Background job: scan Draft emails and send via SMTP with tracking.
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
            
            # v3.5: Provider Factory Logic
            channel = db.query(models.EmailChannelSettings).filter(
                models.EmailChannelSettings.user_id == lead.user_id,
                models.EmailChannelSettings.is_active == True
            ).first()
            
            provider = channel.provider if channel else "smtp"
            
            # Create email log for tracking BEFORE sending
            email_log = email_tracker.create_email_log(
                lead_id=lead.id,
                recipient=to_email,
                subject=campaign.subject,
                template_id=template.id if template else None
            )
            
            try:
                # Process HTML content with tracking
                html_content = campaign.content
                if html_content:
                    # Inject tracking pixel and click redirects
                    processed_html, _ = email_tracker.process_email_content(
                        html_content, email_log.log_uuid
                    )
                else:
                    processed_html = campaign.content

                success = False
                error_msg = ""
                
                # --- Provider Execution ---
                if provider == "postmark" and channel and channel.api_token:
                    from postmark_service import send_postmark_email
                    success, error_msg = send_postmark_email(
                        api_token=channel.api_token,
                        from_email=channel.from_email or channel.user.email,
                        to_email=to_email,
                        subject=campaign.subject,
                        html_body=processed_html,
                        message_stream=channel.message_stream
                    )
                else:
                    # Fallback to SMTP
                    # 1. Check user-specific SMTP
                    user_smtp = db.query(models.SMTPSettings).filter(
                        models.SMTPSettings.user_id == lead.user_id
                    ).first()
                    
                    smtp_config = {
                        "host": user_smtp.smtp_host if user_smtp else SMTP_SERVER,
                        "port": user_smtp.smtp_port if user_smtp else SMTP_PORT,
                        "user": user_smtp.smtp_user if user_smtp else SMTP_USER,
                        "pass": user_smtp.smtp_password if user_smtp else SMTP_PASSWORD,
                        "from": user_smtp.from_email if user_smtp else (channel.from_email if channel else SMTP_USER)
                    }
                    
                    if smtp_config["user"] and smtp_config["pass"]:
                        msg = MIMEMultipart()
                        msg['From'] = smtp_config["from"]
                        msg['To'] = to_email
                        msg['Subject'] = campaign.subject
                        
                        msg.attach(MIMEText(processed_html, 'html' if html_content else 'plain'))

                        # Attach file if template has attachment_url
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

                        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
                            server.starttls()
                            server.login(smtp_config["user"], smtp_config["pass"])
                            server.send_message(msg)
                        
                        success = True
                    else:
                        error_msg = "No valid SMTP or Postmark configuration found"

                if success:
                    # Update status
                    campaign.status = "Sent"
                    lead.status = "Email_Sent"
                    lead.email_sent = True
                    from datetime import datetime
                    lead.email_sent_at = datetime.utcnow()
                    
                    # Update email log
                    email_tracker.update_email_log_status(email_log.log_uuid, "delivered")
                    
                    # v3.5: Billing Check (Email = 1 pt)
                    deduct_points(lead.user_id, "email_sent", {"log_id": email_log.id})
                    
                    add_log(f"✅ [發信] ({provider}) 成功寄送至 {to_email} ({lead.company_name})")
                else:
                    add_log(f"❌ [發信] ({provider}) 失敗: {error_msg}")
                    campaign.status = "Send_Failed"
                    email_tracker.update_email_log_status(email_log.log_uuid, "failed")
                
                db.commit()
                
            except Exception as e:
                add_log(f"❌ [發信] 嚴重錯誤 ({lead.company_name}): {str(e)}")
                campaign.status = "Send_Failed"
                email_tracker.update_email_log_status(email_log.log_uuid, "failed")
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
    
    # v3.5: Crawler Health Heartbeat (Every 12 hours)
    from jobs.health_job import run_health_check_sync
    scheduler.add_job(run_health_check_sync, 'interval', hours=12, id='crawler_health')
    
    scheduler.start()
    add_log("⏰ [排程] 信件發送與爬蟲監聽器已啟動 (v3.5)")

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
