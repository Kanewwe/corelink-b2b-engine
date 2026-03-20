import requests
from bs4 import BeautifulSoup
import time
import models
import ai_service
from database import SessionLocal
from logger import add_log

def scrape_and_process_task(search_url: str, max_pages: int):
    """
    Background task to scrape a directory, extract companies, and AI-process them.
    Note: For highly protected sites like ThomasNet, a headless browser (Selenium) or Apify is recommended.
    This logic assumes a generic directory with basic HTML.
    """
    db = SessionLocal()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    current_page = 1
    
    try:
        while current_page <= max_pages:
            paginated_url = f"{search_url}?page={current_page}" if "?" not in search_url else f"{search_url}&page={current_page}"
            add_log(f"🕷️ [爬蟲] 開始執行網址: {paginated_url}")
            
            response = requests.get(paginated_url, headers=headers, timeout=10)
            if response.status_code != 200:
                add_log(f"❌ [爬蟲] 請求失敗! 狀態碼: {response.status_code}. 可能被阻擋或網址無效。")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- SELECTION LOGIC ---
            # IMPORTANT: Adjust CSS selectors based on the target website.
            # Using generic fallback selectors for MVP:
            company_cards = soup.find_all(['div', 'section'], class_=lambda x: x and ('card' in x or 'profile' in x or 'item' in x))
            if not company_cards:
                company_cards = soup.find_all('h3') # ThomasNet often uses h3 for company names
                
            if not company_cards:
                add_log("⚠️ [爬蟲] 在此頁面找不到任何疑似公司的元件或標題。")
                break
            
            add_log(f"🔎 [爬蟲] 偵測到 {len(company_cards)} 個潛在目標。")

            for card in company_cards:
                company_name = card.text.strip()
                description_tag = card.find_next('p')
                description = description_tag.text.strip() if description_tag else "Business operations and manufacturing."
                
                if len(company_name) < 2:
                    continue

                print(f"[Scraper] Analyzing Company: {company_name[:20]}...")
                
                # Check duplicates
                existing = db.query(models.Lead).filter(models.Lead.company_name == company_name).first()
                if existing:
                    print(f"  -> Skip {company_name} (Already exists)")
                    continue

                # 1. AI Analysis & Tagging
                tag_result = ai_service.analyze_company_and_tag(company_name, description)
                ai_tag = tag_result.get("Tag", "UNKNOWN")
                
                # 2. ONLY proceed if AI found relevant keywords & tag
                if ai_tag != "UNKNOWN":
                    add_log(f"✅ [AI] 判定符合標籤: {ai_tag}. 分派給 {tag_result.get('BD')}")
                    keywords_list = tag_result.get("Keywords", [])
                    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

                    db_lead = models.Lead(
                        company_name=company_name,
                        website_url=None,
                        description=description,
                        extracted_keywords=keywords_str,
                        ai_tag=ai_tag,
                        assigned_bd=tag_result.get("BD", "General"),
                        status="Tagged"
                    )
                    db.add(db_lead)
                    db.commit()
                    db.refresh(db_lead)
                    
                    # 3. Auto-generate Outreach Email Draft immediately
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
                    add_log(f"✉️ [AI] 自動生成開發信草稿成功: {company_name}")
                else:
                    add_log(f"⏭️ [AI] 忽略 (判定為非目標產品線)")
                
                time.sleep(1) # Prevent rate-limiting
                
            current_page += 1
            time.sleep(3) # Delay between pages
            
    except Exception as e:
        print(f"[Scraper] Error during crawl: {str(e)}")
    finally:
        db.close()
        print("[Scraper] Run Completed.")
