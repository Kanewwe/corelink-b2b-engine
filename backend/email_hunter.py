"""
Email Hunter Engine - 角色定向 Email 發現
使用 Hunter.io API 找到採購/負責人 Email
"""

import httpx
import re
import os
import dns.resolver
from typing import Dict, List, Optional
import asyncio

# Hunter.io API Key（免費 25次/月）
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

# 目標角色關鍵字（採購 > 負責人 > 業務主管）
TARGET_ROLES = [
    "procurement", "purchasing", "buyer", "supply chain",
    "owner", "founder", "ceo", "president", "director",
    "general manager", "managing director",
    "sales director", "vp sales", "business development",
    "operations manager"
]

async def find_target_contacts(company_name: str, website_url: str = None, api_key: str = None) -> Dict:
    """
    使用 Hunter.io 找到公司的採購/負責人 Email
    優先級: procurement > owner/CEO > manager > 通用
    """
    key = api_key or HUNTER_API_KEY
    domain = extract_domain(website_url) if website_url else None
    
    if not domain:
        domain = await guess_domain_from_name(company_name)
    
    if not domain:
        return {"emails": [], "domain": None, "mx_valid": False, "contacts": []}
    
    async with httpx.AsyncClient(timeout=15) as client:
        # Step 1: Hunter Domain Search - 取得所有已知聯絡人
        contacts = await hunter_domain_search(client, domain, key)
        
        # Step 2: 角色優先排序
        prioritized = prioritize_contacts(contacts)
        
        # Step 3: MX 驗證
        mx_valid = check_mx_record(domain)
        
        # Step 4: 若 Hunter 找不到，嘗試 pattern 猜測
        if not prioritized and mx_valid:
            prioritized = generate_email_patterns(company_name, domain)
        
        primary = prioritized[0] if prioritized else None
        
        return {
            "domain": domain,
            "mx_valid": mx_valid,
            "contacts": prioritized[:3],  # 最多 3 個目標聯絡人
            "emails": [c["email"] for c in prioritized[:3]],
            "primary_contact": primary
        }

async def find_company_emails(company_name: str, api_key: str = None) -> List[str]:
    """Alias for main.py to get email list directly"""
    result = await find_target_contacts(company_name, api_key=api_key)
    return result.get("emails", [])

async def hunter_domain_search(client: httpx.AsyncClient, domain: str, api_key: str = None) -> List[Dict]:
    """Hunter.io Domain Search API"""
    key = api_key or HUNTER_API_KEY
    if not key:
        return []
    
    url = "https://api.hunter.io/v2/domain-search"
    params = {
        "domain": domain,
        "api_key": key,
        "limit": 20,
        "type": "personal"  # 只找個人信箱，非 info@/contact@
    }
    
    try:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", {}).get("emails", [])
    except Exception as e:
        pass
    return []

def prioritize_contacts(contacts: List[Dict]) -> List[Dict]:
    """依角色優先級排序聯絡人"""
    scored = []
    for contact in contacts:
        position = (contact.get("position") or "").lower()
        score = 0
        
        # 採購優先級最高
        if any(r in position for r in ["procurement", "purchasing", "buyer"]):
            score = 100
        # 負責人次之
        elif any(r in position for r in ["owner", "founder", "ceo", "president"]):
            score = 90
        # 總監/主管
        elif any(r in position for r in ["director", "general manager", "managing director"]):
            score = 80
        # 業務/採購相關
        elif any(r in position for r in ["sales", "business development", "manager"]):
            score = 70
        # 有 confidence > 80 但職位不明
        elif contact.get("confidence", 0) >= 80:
            score = 50
        else:
            score = 10
        
        if score > 0:
            scored.append({**contact, "_priority_score": score})
    
    return sorted(scored, key=lambda x: x["_priority_score"], reverse=True)

def generate_email_patterns(company_name: str, domain: str) -> List[Dict]:
    """當 Hunter 無資料時，生成常見信箱格式"""
    common_patterns = [
        f"procurement@{domain}",
        f"purchasing@{domain}",
        f"buyer@{domain}",
        f"info@{domain}",
        f"contact@{domain}",
        f"sales@{domain}",
    ]
    return [
        {"email": e, "position": "Unknown", "_priority_score": 5, "_is_pattern": True}
        for e in common_patterns[:3]
    ]

def extract_domain(url: str) -> Optional[str]:
    """從 URL 提取根域名"""
    if not url:
        return None
    match = re.search(r'(?:https?://)?(?:www\.)?([^/\s?#]+\.[a-z]{2,})', url.lower())
    return match.group(1) if match else None

async def guess_domain_from_name(company_name: str) -> Optional[str]:
    """透過公司名猜測域名"""
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
    slug = clean.replace(' ', '')[:20]
    
    # 嘗試幾個常見後綴
    candidates = [f"{slug}.com", f"{slug}.co", f"{slug}.net", f"{slug}.io"]
    
    async with httpx.AsyncClient(timeout=5) as client:
        for domain in candidates:
            try:
                resp = await client.head(f"https://{domain}", follow_redirects=True)
                if resp.status_code < 400:
                    return domain
            except:
                continue
    return None

def check_mx_record(domain: str) -> bool:
    """檢查 MX 記錄是否存在"""
    try:
        records = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(records) > 0
    except Exception:
        return False