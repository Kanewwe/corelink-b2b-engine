"""
Email Tracking Service
- Injects tracking pixel (open tracking)
- Injects click redirects (click tracking)
- Handles /track/open and /track/click endpoints
"""

import re
import uuid
import urllib.parse
from bs4 import BeautifulSoup
from database import SessionLocal
import models
from datetime import datetime

# Base URL for tracking (should be configured via environment)
TRACK_BASE_URL = "https://linkoratw.com"  # Will be updated from settings

def set_track_base_url(url: str):
    global TRACK_BASE_URL
    TRACK_BASE_URL = url

def generate_tracking_pixel(log_uuid: str) -> str:
    """Generate HTML for tracking pixel"""
    return f'<img src="{TRACK_BASE_URL}/track/open?id={log_uuid}" width="1" height="1" style="display:none;opacity:0;position:absolute;" alt="" />'

def inject_tracking_pixel(html_content: str, log_uuid: str) -> str:
    """Inject tracking pixel into HTML email content"""
    pixel = generate_tracking_pixel(log_uuid)
    
    # Try to insert before </body>
    if '</body>' in html_content:
        return html_content.replace('</body>', f'{pixel}</body>')
    
    # Otherwise append at the end
    return html_content + pixel

def inject_click_tracking(html_content: str, log_uuid: str) -> str:
    """Replace all links with tracked redirect links"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        tracked_urls = []
        
        for a_tag in soup.find_all('a', href=True):
            original_url = a_tag['href']
            
            # Skip mailto:, tel:, and anchor links
            if original_url.startswith(('mailto:', 'tel:', '#')):
                continue
            
            # Encode the original URL
            encoded_url = urllib.parse.quote(original_url, safe='')
            
            # Replace with tracked URL
            tracked_url = f"{TRACK_BASE_URL}/track/click?id={log_uuid}&url={encoded_url}"
            a_tag['href'] = tracked_url
            
            tracked_urls.append({
                "original": original_url,
                "tracked": tracked_url
            })
        
        return str(soup), tracked_urls
    except Exception as e:
        print(f"Click tracking injection error: {e}")
        return html_content, []

def process_email_content(html_content: str, log_uuid: str) -> tuple:
    """
    Process email HTML to inject all tracking.
    Returns: (processed_html, tracked_urls)
    """
    # First inject click tracking (so we can track the original links)
    html_with_clicks, tracked_urls = inject_click_tracking(html_content, log_uuid)
    
    # Then inject tracking pixel
    html_final = inject_tracking_pixel(html_with_clicks, log_uuid)
    
    return html_final, tracked_urls

# ══════════════════════════════════════════
# Tracking Endpoint Handlers
# ══════════════════════════════════════════

def handle_open_tracking(log_uuid: str) -> tuple:
    """
    Handle tracking pixel request.
    Returns: (response_body, content_type, status_code)
    """
    db = SessionLocal()
    try:
        email_log = db.query(models.EmailLog).filter(
            models.EmailLog.log_uuid == log_uuid
        ).first()
        
        if email_log:
            # Update open tracking
            email_log.opened = True
            email_log.opened_at = datetime.utcnow()
            email_log.open_count = (email_log.open_count or 0) + 1
            db.commit()
            
            # Update lead status if needed
            if email_log.lead:
                email_log.lead.status = "Opened"
                db.commit()
        
        # Return 1x1 transparent PNG
        # This is a minimal valid PNG (1x1 transparent)
        png_1x1 = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return png_1x1, 'image/png', 200
        
    except Exception as e:
        print(f"Open tracking error: {e}")
        return b'', 'image/png', 200  # Still return valid image
    finally:
        db.close()

def handle_click_tracking(log_uuid: str, target_url: str) -> tuple:
    """
    Handle click tracking redirect.
    Returns: (redirect_url, status_code)
    """
    db = SessionLocal()
    try:
        email_log = db.query(models.EmailLog).filter(
            models.EmailLog.log_uuid == log_uuid
        ).first()
        
        if email_log:
            # Update click tracking
            email_log.clicked = True
            email_log.clicked_at = datetime.utcnow()
            email_log.click_count = (email_log.click_count or 0) + 1
            
            # Track which URLs were clicked
            clicked_urls = email_log.clicked_urls or []
            decoded_url = urllib.parse.unquote(target_url)
            
            # Find or create URL entry
            url_found = False
            for entry in clicked_urls:
                if entry.get("url") == decoded_url:
                    entry["count"] = entry.get("count", 0) + 1
                    url_found = True
                    break
            
            if not url_found:
                clicked_urls.append({"url": decoded_url, "count": 1})
            
            email_log.clicked_urls = clicked_urls
            db.commit()
            
            # Update lead status if needed
            if email_log.lead:
                email_log.lead.status = "Clicked"
                db.commit()
        
        # Return redirect to target URL
        decoded_url = urllib.parse.unquote(target_url)
        return decoded_url, 302
        
    except Exception as e:
        print(f"Click tracking error: {e}")
        # Fallback: try to redirect anyway
        return urllib.parse.unquote(target_url), 302
    finally:
        db.close()

# ══════════════════════════════════════════
# Email Log Creation
# ══════════════════════════════════════════

def create_email_log(
    lead_id: int,
    recipient: str,
    subject: str,
    template_id: int = None
) -> models.EmailLog:
    """Create a new email log entry before sending"""
    db = SessionLocal()
    try:
        log_uuid = str(uuid.uuid4())
        
        email_log = models.EmailLog(
            log_uuid=log_uuid,
            lead_id=lead_id,
            template_id=template_id,
            recipient=recipient,
            subject=subject,
            status="pending"
        )
        
        db.add(email_log)
        db.commit()
        db.refresh(email_log)
        
        return email_log
        
    finally:
        db.close()

def update_email_log_status(log_uuid: str, status: str):
    """Update email log delivery status"""
    db = SessionLocal()
    try:
        email_log = db.query(models.EmailLog).filter(
            models.EmailLog.log_uuid == log_uuid
        ).first()
        
        if email_log:
            email_log.status = status
            db.commit()
            
    finally:
        db.close()

def mark_email_replied(log_uuid: str, source: str = "manual"):
    """Mark email as replied"""
    db = SessionLocal()
    try:
        email_log = db.query(models.EmailLog).filter(
            models.EmailLog.log_uuid == log_uuid
        ).first()
        
        if email_log:
            email_log.replied = True
            email_log.replied_at = datetime.utcnow()
            email_log.reply_source = source
            db.commit()
            
    finally:
        db.close()

def get_engagement_stats() -> dict:
    """Get overall engagement statistics"""
    db = SessionLocal()
    try:
        total = db.query(models.EmailLog).count()
        delivered = db.query(models.EmailLog).filter(
            models.EmailLog.status == "delivered"
        ).count()
        opened = db.query(models.EmailLog).filter(
            models.EmailLog.opened == True
        ).count()
        clicked = db.query(models.EmailLog).filter(
            models.EmailLog.clicked == True
        ).count()
        replied = db.query(models.EmailLog).filter(
            models.EmailLog.replied == True
        ).count()
        
        return {
            "total_sent": total,
            "delivered": delivered,
            "delivered_rate": round(delivered / total * 100, 1) if total > 0 else 0,
            "opened": opened,
            "open_rate": round(opened / delivered * 100, 1) if delivered > 0 else 0,
            "clicked": clicked,
            "click_rate": round(clicked / opened * 100, 1) if opened > 0 else 0,
            "replied": replied,
            "reply_rate": round(replied / opened * 100, 1) if opened > 0 else 0
        }
        
    finally:
        db.close()
