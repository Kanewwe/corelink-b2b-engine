import pytest
import models
from scrape_utils import sync_from_global_pool, save_to_global_pool

def test_global_pool_persistence_and_sync(db_session):
    """
    核心業務流程驗證：全域資料池 (Global Pool) 同步機制。
    1. 爬蟲抓到資料後存入 Global Pool。
    2. 其他用戶搜尋相同 Domain 時，應從 Global Pool 同步，而非重新爬取。
    """
    # 1. 模擬爬蟲抓到一筆資料並存入全域池
    raw_data = {
        "company_name": "Tesla Inc",
        "domain": "tesla.com",
        "website_url": "https://tesla.com",
        "contact_email": "hello@tesla.com",
        "industry_taxonomy": "Automotive > EV",
        "source": "manual_test"
    }
    
    global_lead = save_to_global_pool(db_session, raw_data)
    assert global_lead.id is not None
    assert global_lead.company_name == "Tesla Inc"
    
    # 2. 建立一個新用戶 User B
    user_b = models.User(email="user_b@test.com", name="User B")
    user_b.set_password("pass123")
    db_session.add(user_b)
    db_session.commit()
    
    # 3. User B 嘗試同步這筆資料 (模擬搜尋 domain)
    synced_lead, is_new = sync_from_global_pool(db_session, user_b.id, domain="tesla.com")
    
    # 驗證同步結果
    assert is_new is True
    assert synced_lead.company_name == "Tesla Inc"
    assert synced_lead.user_id == user_b.id
    assert synced_lead.global_id == global_lead.id
    assert synced_lead.status == "Synced"

def test_domain_deduplication(db_session):
    """
    驗證 Domain 去重邏輯。
    """
    user_a = models.User(email="user_a@test.com", name="User A")
    user_a.set_password("pass123")
    db_session.add(user_a)
    db_session.commit()
    
    # 存入第一筆
    save_to_global_pool(db_session, {"company_name": "Apple", "domain": "apple.com"})
    
    # 存入第二筆相同 Domain 但不同名稱 (應更新或跳過)
    save_to_global_pool(db_session, {"company_name": "Apple Inc", "domain": "apple.com"})
    
    count = db_session.query(models.GlobalLead).filter(models.GlobalLead.domain == "apple.com").count()
    assert count == 1
    
    g_lead = db_session.query(models.GlobalLead).filter(models.GlobalLead.domain == "apple.com").first()
    assert g_lead.company_name == "Apple Inc" # 預期為更新後的名稱

def test_sync_disabled_scenario(db_session):
    """
    驗證當同步功能關閉時，不應從全域池拉取資料。
    """
    user_c = models.User(email="user_c@test.com", name="User C")
    user_c.set_password("pass123")
    db_session.add(user_c)
    db_session.commit()
    
    # 全域池已有資料
    save_to_global_pool(db_session, {"company_name": "Google", "domain": "google.com"})
    
    # 同步關閉 (sync_enabled=False)
    synced_lead, is_new = sync_from_global_pool(db_session, user_c.id, domain="google.com", sync_enabled=False)
    
    assert synced_lead is None
    assert is_new is False
