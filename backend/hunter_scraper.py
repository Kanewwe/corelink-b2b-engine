"""
Hunter.io Scraper Module (v3.7.30)
Email discovery and verification using Hunter.io API
"""
import os
import requests
from typing import Optional, List, Dict
from logger import add_log

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "4e8ab26df6a9bf8216fa30afca375966cb135523")
HUNTER_BASE_URL = "https://api.hunter.io/v2"


class HunterScraper:
    """Hunter.io Email Finder"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or HUNTER_API_KEY
        self.base_url = HUNTER_BASE_URL
    
    def domain_search(
        self, 
        domain: str, 
        limit: int = 10,
        seniority: str = None,
        department: str = None
    ) -> Dict:
        """
        Search emails by domain
        
        Args:
            domain: Company domain (e.g., "company.com")
            limit: Max results (default 10)
            seniority: Filter by seniority (junior, senior, executive)
            department: Filter by department (executive, it, finance, ...
        
        Returns:
            {
                "success": True,
                "emails": [...],
                "total": 50,
                "source": "hunter"
            }
        """
        try:
            params = {
                "domain": domain,
                "api_key": self.api_key,
                "limit": limit
            }
            
            if seniority:
                params["seniority"] = seniority
            if department:
                params["department"] = department
            
            resp = requests.get(
                f"{self.base_url}/domain-search",
                params=params,
                timeout=15
            )
            
            if resp.status_code != 200:
                error = resp.json().get("errors", [{}])[0]
                return {
                    "success": False,
                    "error": error.get("details", "Unknown error"),
                    "domain": domain
                }
            
            data = resp.json().get("data", {})
            emails = data.get("emails", [])
            
            # 整理結果
            result = {
                "success": True,
                "domain": domain,
                "total": data.get("total", 0),
                "emails": [],
                "source": "hunter"
            }
            
            for email in emails:
                result["emails"].append({
                    "email": email.get("value"),
                    "type": email.get("type"),
                    "first_name": email.get("first_name"),
                    "last_name": email.get("last_name"),
                    "position": email.get("position"),
                    "department": email.get("department"),
                    "seniority": email.get("seniority"),
                    "confidence": email.get("confidence", 0),
                    "verified": email.get("verification", {}).get("status") == "valid",
                    "linkedin": email.get("linkedin"),
                    "twitter": email.get("twitter")
                })
            
            add_log(f"Hunter: {domain} → {len(result['emails'])} emails")
            return result
            
        except Exception as e:
            add_log(f"⚠️ Hunter error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain
            }
    
    def email_finder(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> Dict:
        """
        Find specific person's email
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            domain: Company domain
        
        Returns:
            {
                "success": True,
                "email": "john@company.com",
                "confidence": 95,
                "verified": True
            }
        """
        try:
            resp = requests.get(
                f"{self.base_url}/email-finder",
                params={
                    "first_name": first_name,
                    "last_name": last_name,
                    "domain": domain,
                    "api_key": self.api_key
                },
                timeout=15
            )
            
            if resp.status_code != 200:
                error = resp.json().get("errors", [{}])[0]
                return {
                    "success": False,
                    "error": error.get("details", "Unknown error")
                }
            
            data = resp.json().get("data", {})
            
            return {
                "success": True,
                "email": data.get("email"),
                "confidence": data.get("score", 0),
                "verified": data.get("verification", {}).get("status") == "valid",
                "first_name": first_name,
                "last_name": last_name,
                "domain": domain
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def email_verifier(self, email: str) -> Dict:
        """
        Verify email deliverability
        
        Args:
            email: Email address to verify
        
        Returns:
            {
                "success": True,
                "email": "test@company.com",
                "status": "valid"|"invalid"|"accept_all"|"webmail",
                "confidence": 95
            }
        """
        try:
            resp = requests.get(
                f"{self.base_url}/email-verifier",
                params={
                    "email": email,
                    "api_key": self.api_key
                },
                timeout=15
            )
            
            if resp.status_code != 200:
                return {
                    "success": False,
                    "email": email,
                    "error": "Verification failed"
                }
            
            data = resp.json().get("data", {})
            
            return {
                "success": True,
                "email": email,
                "status": data.get("status"),
                "confidence": data.get("score", 0),
                "smtp_check": data.get("smtp_check"),
                "accept_all": data.get("accept_all")
            }
            
        except Exception as e:
            return {
                "success": False,
                "email": email,
                "error": str(e)
            }
    
    def get_account_info(self) -> Dict:
        """Get account info and remaining quota"""
        try:
            resp = requests.get(
                f"{self.base_url}/account",
                params={"api_key": self.api_key},
                timeout=10
            )
            
            if resp.status_code != 200:
                return {"success": False}
            
            data = resp.json().get("data", {})
            
            return {
                "success": True,
                "email": data.get("email"),
                "plan": data.get("plan_name"),
                "calls_remaining": data.get("calls", {}).get("remaining"),
                "calls_used": data.get("calls", {}).get("used")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def infer_industry(company_name: str, description: str = None) -> Dict:
    """
    Infer industry from company name and description
    
    Returns:
        {
            "industry_code": "MFG-ELEC",
            "industry_name": "電子製造",
            "industry_tags": "電子,PCB,半導體"
        }
    """
    text = f"{company_name} {description or ''}".lower()
    
    # 關鍵字匹配規則
    rules = [
        (["electronics", "pcb", "半導體", "電子", "circuit"], "MFG-ELEC", "電子製造", "電子,PCB,半導體"),
        (["machinery", "cnc", "機械", "車床"], "MFG-MECH", "機械製造", "機械,CNC"),
        (["software", "app", "軟體", "saas", "科技"], "TECH-SOFTWARE", "軟體開發", "軟體,SaaS"),
        (["semiconductor", "ic", "晶圓"], "TECH-SEMICON", "半導體", "半導體,晶圓,IC"),
        (["ecommerce", "電商", "網購"], "RETAIL-ECOMMERCE", "電商平台", "電商,網購"),
        (["restaurant", "餐廳", "美食"], "SERVICE-RESTAURANT", "餐飲", "餐廳,美食"),
        (["hospital", "醫院", "診所"], "HEALTH-HOSPITAL", "醫院診所", "醫院,診所"),
        (["construction", "建設", "工程"], "CONST-BUILD", "建設公司", "建設,工程"),
        (["logistics", "物流", "貨運"], "TRANS-FREIGHT", "貨運", "物流,貨運"),
        (["solar", "太陽能", "光電"], "ENERGY-SOLAR", "太陽能", "太陽能,光電"),
    ]
    
    for keywords, code, name, tags in rules:
        if any(kw in text for kw in keywords):
            return {
                "industry_code": code,
                "industry_name": name,
                "industry_tags": tags
            }
    
    # 預設返回製造業
    return {
        "industry_code": "MFG",
        "industry_name": "製造業",
        "industry_tags": "製造"
    }


# 便捷函數
def search_domain_emails(domain: str, limit: int = 10) -> Dict:
    """Search emails by domain"""
    scraper = HunterScraper()
    return scraper.domain_search(domain, limit)


def find_person_email(first_name: str, last_name: str, domain: str) -> Dict:
    """Find specific person's email"""
    scraper = HunterScraper()
    return scraper.email_finder(first_name, last_name, domain)


def verify_email(email: str) -> Dict:
    """Verify email deliverability"""
    scraper = HunterScraper()
    return scraper.email_verifier(email)
