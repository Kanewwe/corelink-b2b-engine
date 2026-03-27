"""
Scrape Utilities (v2.7) - Lead Isolation Pool Sync
處理 GlobalPool 與 Private Leads 之間的同步邏輯。
"""

import models
from datetime import datetime
from logger import add_log

def extract_best_email(item: dict):
    """
    從爬蟲回傳的 item 中提取最合適的 Email。
    優先順序: contactEmail > emails (list FIRST) > email (string)
    """
    if not item: return ""
    
    # 1. 優先取 contactEmail
    ce = item.get("contactEmail")
    if ce and isinstance(ce, str) and "@" in ce:
        return ce.strip().lower()
        
    # 2. 檢查 emails 列表
    emails = item.get("emails")
    if emails and isinstance(emails, list):
        for e in emails:
            if e and isinstance(e, str) and "@" in e:
                # 排除一些常見的垃圾/通用前綴 (可加強)
                return e.strip().lower()
    
    # 3. 檢查單一 email 欄位
    e = item.get("email")
    if e and isinstance(e, str) and "@" in e:
        return e.strip().lower()
        
    return ""

def sync_from_global_pool(db, user_id: int, domain: str = None, company_name: str = None, sync_enabled: bool = True):
    """
    從全域隔離池 (Global Pool) 同步資料到私有清單。
    v2.7.1: 支援 sync_enabled 開關。
    回傳: (Lead 對象, is_new: bool)
    """
    if not domain and not company_name:
        return None, False
        
    # 1. 檢查私有清單是否已有 (無論開關如何，私有去重都要做)
    existing_private = None
    if domain:
        existing_private = db.query(models.Lead).filter(
            models.Lead.domain == domain,
            models.Lead.user_id == user_id
        ).first()
    
    if not existing_private:
        existing_private = db.query(models.Lead).filter(
            models.Lead.company_name == company_name,
            models.Lead.user_id == user_id
        ).first()
        
    if existing_private:
        return existing_private, False
        
    # 2. 檢索全域池 (Global Pool) - 僅在同步開啟時進行 (v2.7.1)
    if not sync_enabled:
        return None, False

    global_lead = None
    if domain:
        global_lead = db.query(models.GlobalLead).filter(models.GlobalLead.domain == domain).first()
    
    if not global_lead:
        global_lead = db.query(models.GlobalLead).filter(models.GlobalLead.company_name == company_name).first()
        
    if global_lead:
        # 同步回私有清單 (v3.0: 雙層架構)
        new_lead = models.Lead(
            user_id=user_id,
            global_id=global_lead.id,
            company_name=global_lead.company_name,
            website_url=global_lead.website_url,
            domain=global_lead.domain,
            contact_email=global_lead.contact_email,
            email_candidates=global_lead.email_candidates,
            phone=global_lead.phone,
            address=global_lead.address,
            ai_tag=global_lead.ai_tag,
            industry_taxonomy=global_lead.industry_taxonomy, # v3.0
            status="Synced",
            assigned_bd="Global-Pool-Sync",
            # 初始化 Overlay 欄位為 None
            override_name=None,
            override_email=None,
            personal_notes=None,
            custom_tags=None
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        add_log(f"🔄 [GlobalSync] 從全域池同步：{global_lead.company_name}")
        return new_lead, True
        
    return None, False

def save_to_global_pool(db, lead_data: dict):
    """
    將採集到的資料存入/更新全域隔離池。
    回傳: GlobalLead 對象
    """
    domain = lead_data.get("domain")
    name = lead_data.get("company_name")
    
    if not domain and not name:
        return None
        
    # 優先使用 Domain 作為唯一鍵
    global_lead = None
    if domain:
        global_lead = db.query(models.GlobalLead).filter(models.GlobalLead.domain == domain).first()
    else:
        global_lead = db.query(models.GlobalLead).filter(models.GlobalLead.company_name == name).first()
        
    if not global_lead:
        global_lead = models.GlobalLead(
            company_name=name,
            domain=domain,
            website_url=lead_data.get("website_url"),
            description=lead_data.get("description"),
            contact_email=lead_data.get("contact_email"),
            email_candidates=lead_data.get("email_candidates"),
            phone=lead_data.get("phone"),
            address=lead_data.get("address"),
            ai_tag=lead_data.get("ai_tag"),
            source=lead_data.get("source")
        )
        db.add(global_lead)
        add_log(f"🆕 [GlobalPool] 新增資料：{name}")
    else:
        # 更新資料（優化 Email 更新與內容補足）
        global_lead.company_name = name or global_lead.company_name
        global_lead.website_url = lead_data.get("website_url") or global_lead.website_url
        
        # 關鍵：若全域池原本缺 Email，但這次抓到了，則補足
        new_email = lead_data.get("contact_email")
        if new_email and (not global_lead.contact_email or global_lead.contact_email != new_email):
            global_lead.contact_email = new_email
            add_log(f"📧 [GlobalPool] 補足 Email：{name} -> {new_email}")
            
        if lead_data.get("description") and (not global_lead.description or len(lead_data.get("description")) > len(global_lead.description)):
             global_lead.description = lead_data.get("description")
             
        global_lead.last_scraped_at = datetime.utcnow()
        
    db.commit()
    db.refresh(global_lead)
    return global_lead
