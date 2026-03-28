import pytest
import models
import uuid
from email_tracker import inject_tracking_pixel, inject_click_tracking

def test_tracking_injection_logic():
    """
    驗證追蹤代碼注入邏輯。
    """
    html_content = "<html><body><h1>Hello World</h1><a href='https://google.com'>Link</a></body></html>"
    log_uuid = "test-uuid-123"
    
    # 1. 驗證 Pixel 注入
    html_with_pixel = inject_tracking_pixel(html_content, log_uuid)
    assert f"track/open?id={log_uuid}" in html_with_pixel
    assert "</body>" in html_with_pixel
    
    # 2. 驗證點擊追蹤注入
    html_with_clicks, tracked_urls = inject_click_tracking(html_content, log_uuid)
    assert f"track/click?id={log_uuid}" in html_with_clicks
    assert len(tracked_urls) == 1
    assert tracked_urls[0]["original"] == "https://google.com"

def test_email_log_status_updates(db_session):
    """
    驗證 EmailLog 的狀態更新邏輯。
    """
    # 建立測試資料
    user = models.User(email="sender@test.com", name="Sender")
    user.set_password("pass123")
    db_session.add(user)
    
    lead = models.Lead(company_name="Target Corp", user_id=user.id)
    db_session.add(lead)
    db_session.commit()
    
    log_uuid = str(uuid.uuid4())
    email_log = models.EmailLog(
        log_uuid=log_uuid,
        lead_id=lead.id,
        recipient="target@test.com",
        subject="Test Subject",
        status="pending"
    )
    db_session.add(email_log)
    db_session.commit()
    
    # 模擬開信 (手動更新 DB 欄位，模擬 handle_open_tracking 的行為)
    email_log.opened = True
    email_log.opened_at = models.datetime.utcnow()
    email_log.open_count = 1
    lead.status = "Opened"
    db_session.commit()
    
    # 驗證
    updated_log = db_session.query(models.EmailLog).filter(models.EmailLog.log_uuid == log_uuid).first()
    assert updated_log.opened is True
    assert updated_log.lead.status == "Opened"

def test_campaign_linkage(db_session):
    """
    驗證 Campaign 與 Lead 的關聯。
    """
    user = models.User(email="user@test.com")
    user.set_password("pass123")
    db_session.add(user)
    
    lead = models.Lead(company_name="My Lead", user_id=user.id)
    db_session.add(lead)
    db_session.commit()
    
    campaign = models.EmailCampaign(
        user_id=user.id,
        lead_id=lead.id,
        subject="Campaign Subject",
        content="Content",
        status="Sent"
    )
    db_session.add(campaign)
    db_session.commit()
    
    # 從 Lead 查 Campaign
    assert len(lead.email_campaigns) == 1
    assert lead.email_campaigns[0].subject == "Campaign Subject"
