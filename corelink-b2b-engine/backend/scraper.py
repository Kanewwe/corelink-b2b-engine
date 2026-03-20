import requests
from bs4 import BeautifulSoup
import time
import models
import ai_service
from database import SessionLocal
from logger import add_log

def clean_company_name(title: str, domain: str) -> str:
    """Removes the directory domain name and SEO spam from the title."""
    clean = title.replace(f" - {domain}", "").replace(f" | {domain}", "").replace(domain, "")
    return clean.split('|')[0].split('-')[0].strip()

def scrape_and_process_task(market: str, keyword: str):
    """
    Background task to mine companies using Search Dorking over multiple directories.
    This avoids direct 403 Forbidden rules set by Cloudflare on Yellowpages etc.
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
    
    add_log(f"蜘蛛 [探勘] 啟動全自動尋機！市場: {market}, 關鍵字: '{keyword}'")

    try:
        for domain in target_domains:
            query = f"site:{domain} {keyword}"
            add_log(f"🔎 [探勘] 正在分析 {domain} 的網路目錄資料...")
            
            url = "https://html.duckduckgo.com/html/"
            response = requests.post(url, data={"q": query}, headers=headers, timeout=15)
            
            if response.status_code != 200:
                add_log(f"⚠️ [探勘] 遭受速率限制或存取失敗 (Status: {response.status_code})，跳過 {domain}。")
                time.sleep(5)
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='result')
            
            if not results:
                add_log(f"📉 [探勘] 在 {domain} 找不到與 '{keyword}' 相關的合格廠商。")
                time.sleep(3)
                continue
                
            add_log(f"🎯 [探勘] 於 {domain} 發現 {len(results)} 筆可能名單，開始讓 AI 進行鑑定。")
            
            # Take top 5 per directory to avoid getting banned or API throttling
            for res in results[:5]: 
                title_elem = res.find('a', class_='result__url')
                snippet_elem = res.find('a', class_='result__snippet')
                
                if not title_elem or not snippet_elem:
                    continue
                    
                raw_title = title_elem.text.strip()
                description = snippet_elem.text.strip()
                company_name = clean_company_name(raw_title, domain)
                
                if len(company_name) < 2:
                    continue

                add_log(f"🧠 [AI] 正在解析特徵 -> {company_name[:20]}...")
                
                # Check duplicates in database
                existing = db.query(models.Lead).filter(models.Lead.company_name == company_name).first()
                if existing:
                    add_log(f"⏭️ [AI] 自動略過 (資料庫已存在同名企業)")
                    continue

                # 1. AI Analysis & Tagging
                tag_result = ai_service.analyze_company_and_tag(company_name, description)
                ai_tag = tag_result.get("Tag", "UNKNOWN")
                
                if ai_tag != "UNKNOWN":
                    add_log(f"✅ [AI] 精準鎖定產品標籤: {ai_tag}. 指派業務: {tag_result.get('BD')}")
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
                    add_log(f"✉️ [AI] 開發信專屬草稿已產生: {company_name}")
                else:
                    add_log(f"⏭️ [AI] 忽略 (無法確定目標產業 / {company_name})")
                
                time.sleep(2) # Prevent OpenAI API rate limits
                
            time.sleep(5) # Delay between directories to respect limits
            
    except Exception as e:
        add_log(f"❌ [尋機] 發生嚴重錯誤: {str(e)}")
    finally:
        db.close()
        add_log("🏁 [尋機] 全自動多平台背景探勘任務圓滿執行完畢！")
