"""
Scrape Utilities (v2.7) - Lead Isolation Pool Sync
處理 GlobalPool 與 Private Leads 之間的同步邏輯。
"""

import models
from datetime import datetime
from logger import add_log

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
        # 同步回私有清單
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
            status="Synced",
            assigned_bd="Global-Pool-Sync"
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
    else:
        # 更新資料（保留現有 email 如果新的比較差，這裡可做更複雜邏輯）
        global_lead.company_name = name
        global_lead.website_url = lead_data.get("website_url") or global_lead.website_url
        global_lead.contact_email = lead_data.get("contact_email") or global_lead.contact_email
        global_lead.last_scraped_at = datetime.utcnow()
        
    db.commit()
    db.refresh(global_lead)
    return global_lead
