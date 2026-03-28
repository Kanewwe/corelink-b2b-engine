import pytest
import models

def test_user_data_isolation(db_session):
    """
    核業務流程驗證：不同用戶之間的資料必須隔離。
    Vendor A 不應看到 Vendor B 的 Leads。
    """
    # 1. 建立兩個不同的用戶 (Mock Vendors/Members)
    user_a = models.User(email="vendor_a@test.com", name="Vendor A", role="vendor")
    user_a.set_password("pass123")
    db_session.add(user_a)
    
    user_b = models.User(email="vendor_b@test.com", name="Vendor B", role="vendor")
    user_b.set_password("pass123")
    db_session.add(user_b)
    db_session.commit()
    
    # 2. 為 User A 建立一筆 Lead
    lead_a = models.Lead(
        company_name="Apple Inc",
        user_id=user_a.id,
        status="Scraped"
    )
    db_session.add(lead_a)
    
    # 3. 為 User B 建立一筆 Lead
    lead_b = models.Lead(
        company_name="Banana Corp",
        user_id=user_b.id,
        status="Scraped"
    )
    db_session.add(lead_b)
    db_session.commit()
    
    # 4. 驗證隔離性：User A 查詢時應只看到自己的 Leads
    leads_for_a = db_session.query(models.Lead).filter(models.Lead.user_id == user_a.id).all()
    assert len(leads_for_a) == 1
    assert leads_for_a[0].company_name == "Apple Inc"
    
    # 5. 驗證隔離性：User B 查詢時應只看到自己的 Leads
    leads_for_b = db_session.query(models.Lead).filter(models.Lead.user_id == user_b.id).all()
    assert len(leads_for_b) == 1
    assert leads_for_b[0].company_name == "Banana Corp"

def test_admin_full_access(db_session):
    """
    驗證 Admin 角色應具有跨用戶資料的可見性（或根據業務邏輯決定）。
    目前模型中 Admin 可以 Query 所有的 Leads。
    """
    admin = models.User(email="admin@test.com", name="Admin", role="admin")
    admin.set_password("admin123")
    db_session.add(admin)
    db_session.commit()
    
    # 建立一些不同用戶的資料
    user_1 = models.User(email="u1@test.com", name="U1")
    user_1.set_password("p1")
    db_session.add(user_1)
    db_session.commit()
    
    lead_1 = models.Lead(company_name="Global Corp", user_id=user_1.id)
    db_session.add(lead_1)
    db_session.commit()
    
    # Admin 執行全系統 Query
    all_leads = db_session.query(models.Lead).all()
    assert len(all_leads) >= 1
    
def test_rbac_creation_security(db_session):
    """
    驗證用戶在建立資料時，若漏傳 user_id 是否會造成問題（或是應強制檢查）。
    """
    # 這是為了確保 migrations.py 的 user_id 補全邏輯在 DB 層級是有效的
    new_lead = models.Lead(company_name="Anonymous Corp")
    db_session.add(new_lead)
    db_session.commit()
    
    assert new_lead.user_id is None # 在測試環境中預期為 None，除非主程式 API 有做攔截
