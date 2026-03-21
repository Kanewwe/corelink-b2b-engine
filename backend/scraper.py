import requests
from bs4 import BeautifulSoup
import time
import models
import ai_service
import email_finder
from database import SessionLocal
from logger import add_log
import asyncio

def clean_company_name(title: str, domain: str) -> str:
    """Removes the directory domain name and SEO spam from the title."""
    clean = title.replace(f" - {domain}", "").replace(f" | {domain}", "").replace(domain, "")
    return clean.split('|')[0].split('-')[0].strip()

def check_company_exists(db, company_name: str, domain: str = None) -> tuple:
    """
    Check if company already exists in database.
    Returns: (exists: bool, reason: str, lead_object)
    """
    # Check by exact company name
    existing = db.query(models.Lead).filter(
        models.Lead.company_name == company_name
    ).first()
    
    if existing:
        if existing.email_sent:
            return True, f"已寄過信 ({existing.email_sent_at.strftime('%Y-%m-%d')})", existing
        return True, "資料庫已存在", existing
    
    # Check by domain if available
    if domain:
        existing_domain = db.query(models.Lead).filter(
            models.Lead.domain == domain
        ).first()
        if existing_domain:
            if existing_domain.email_sent:
                return True, f"網域已寄過信 ({existing_domain.email_sent_at.strftime('%Y-%m-%d')})", existing_domain
            return True, "網域已存在", existing_domain
    
    return False, None, None

def scrape_and_process_task(market: str, keyword: str):
    """
    Background task to mine companies with duplicate checking and email sent tracking.
    """
    db = SessionLocal()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }

    directories = {
        "US": ["yellowpages.com", "superpages.com", "yelp.com"],
        "EU": ["europages.com", "yell.com", "pagesjaunes.fr", "gelbeseiten.de"]
    }
    
    target_domains = directories.get(market, directories["US"])
    
    add_log(f"🔍 [探勘] 啟動全自動尋機！市場: {market}, 關鍵字: '{keyword}'")
    
    stats = {
        "found": 0,
        "skipped_duplicate": 0,
        "skipped_emailed": 0,
        "new": 0
    }

    try:
        for domain in target_domains:
            query = f"site:{domain} {keyword}"
            add_log(f"🔎 [探勘] 正在分析 {domain}...")
            
            url = f"https://search.yahoo.com/search?p={query}"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                add_log(f"⚠️ [探勘] 存取失敗 (Status: {response.status_code})，跳過 {domain}")
                time.sleep(5)
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='algo')
            
            if not results:
                add_log(f"📉 [探勘] 在 {domain} 找不到相關廠商")
                time.sleep(3)
                continue
                
            add_log(f"🎯 [探勘] 於 {domain} 發現 {len(results)} 筆可能名單")
            
            for res in results[:5]: 
                title_elem = res.find('h3')
                snippet_elem = res.find('div', class_='compText')
                
                if not title_elem:
                    continue
                    
                raw_title = title_elem.text.strip()
                description = snippet_elem.text.strip() if snippet_elem else "Business detail."
                company_name = clean_company_name(raw_title, domain)
                
                if len(company_name) < 2:
                    continue

                stats["found"] += 1
                add_log(f"🧠 [分析] {company_name[:30]}...")
                
                # Check for duplicates with email sent tracking
                exists, reason, existing_lead = check_company_exists(db, company_name)
                
                if exists:
                    if existing_lead and existing_lead.email_sent:
                        stats["skipped_emailed"] += 1
                        add_log(f"📧 [跳過] {company_name[:20]} - {reason}")
                    else:
                        stats["skipped_duplicate"] += 1
                        add_log(f"⏭️ [跳過] {company_name[:20]} - {reason}")
                    continue

                # Rule-based Classification
                tag_result = ai_service.analyze_company_and_tag(company_name, description, use_gpt=False)
                ai_tag = tag_result.get("Tag", "UNKNOWN")
                
                if ai_tag == "UNKNOWN":
                    add_log(f"⏭️ [忽略] 無法分類: {company_name[:20]}")
                    continue
                
                add_log(f"✅ [分類] {ai_tag} -> {tag_result.get('BD')}")
                keywords_list = tag_result.get("Keywords", [])
                keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

                # Auto-discover email
                add_log(f"📧 [Email] 尋找 {company_name[:20]}...")
                email_info = asyncio.run(email_finder.find_emails_for_company(company_name))
                
                discovered_domain = email_info.get("domain")
                mx_valid = email_info.get("mx_valid", False)
                email_candidates = email_info.get("emails", [])
                email_str = ", ".join(email_candidates) if email_candidates else None
                
                if discovered_domain:
                    add_log(f"🌐 [Email] {discovered_domain} | MX: {'✅' if mx_valid else '❌'}")

                # Save Lead
                db_lead = models.Lead(
                    company_name=company_name,
                    website_url=discovered_domain,
                    domain=discovered_domain,
                    email_candidates=email_str,
                    mx_valid=1 if mx_valid else 0,
                    description=description,
                    extracted_keywords=keywords_str,
                    ai_tag=ai_tag,
                    assigned_bd=tag_result.get("BD", "General"),
                    status="Tagged"
                )
                db.add(db_lead)
                db.commit()
                db.refresh(db_lead)
                stats["new"] += 1
                
                # Generate email draft
                k_list = [k.strip() for k in keywords_str.split(',')] if keywords_str else []
                email_result = ai_service.generate_outreach_email(
                    company_name, description, ai_tag, db_lead.assigned_bd, k_list
                )
                
                campaign = models.EmailCampaign(
                    lead_id=db_lead.id,
                    subject=email_result.get("Subject", "Corelink Partnership"),
                    content=email_result.get("Body", ""),
                    status="Draft"
                )
                db.add(campaign)
                db_lead.status = "Email_Drafted"
                db.commit()
                add_log(f"✉️ [完成] {company_name[:20]} - 草稿已生成")
                
                time.sleep(2)
                
            time.sleep(5)
            
    except Exception as e:
        add_log(f"❌ [錯誤] {str(e)}")
    finally:
        db.close()
        add_log(f"🏁 [完成] 探勘結束！發現:{stats['found']} 新増:{stats['new']} 跳過(重複):{stats['skipped_duplicate']} 跳過(已寄信):{stats['skipped_emailed']}")
