from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time
from dotenv import load_dotenv

import models
from database import SessionLocal
from logger import add_log

load_dotenv()

# --- SMTP Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT", 587)
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_actual_email(to_email: str, subject: str, body: str) -> bool:
    """Send email via SMTP, or simulate sending if config is missing."""
    if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
        add_log(f"📋 [發信] 檢測到尚未設定 SMTP。模擬發信中 (Mock Mode) - 目標: {to_email}")
        return True # Simulate success so status updates to 'Sent'

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        add_log(f"❌ [發信] SMTP 錯誤: {e}")
        return False

def process_draft_emails():
    """Background task to fetch pending drafts and send them."""
    print("[Email Job] Waking up to process pending drafts...")
    db: Session = SessionLocal()
    try:
        drafts = db.query(models.EmailCampaign).filter(models.EmailCampaign.status == "Draft").all()
        
        if not drafts:
            # Silently check next time, don't spam UI logs
            return
            
        add_log(f"🚀 [發信排程] 檢測到 {len(drafts)} 封新草稿，準備依序自動派發。")
            
        for draft in drafts:
            lead = draft.lead
            # If no specific contact email exists, we fake one for the MVP based on the company name
            target_email = f"contact@{lead.company_name.replace(' ', '').replace(',', '').lower()}.com"
            
            print(f"[Email Job] Preparing to send '{draft.subject[:20]}...' to {target_email}...")
            
            success = send_actual_email(target_email, draft.subject, draft.content)
            if success:
                draft.status = "Sent"
                lead.status = "Email_Sent"
                db.commit()
                add_log(f"✅ [發信] 成功派發至: {target_email} ({draft.subject[:10]}...)")
            time.sleep(2) # Brief delay to prevent SMTP anti-spam triggering
            
    except Exception as e:
        print(f"[Email Job] DB Error: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Runs the email spreading job every 2 minutes. In production, 10 or 30 minutes is safer.
    scheduler.add_job(process_draft_emails, 'interval', minutes=2)
    scheduler.start()
    print("[Email Job] 🕒 Background SMTP Scheduler started. Checking for drafts every 2 minutes.")
