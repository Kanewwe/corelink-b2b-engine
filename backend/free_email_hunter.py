"""
免費 Email 發現系統 - 三層策略
Layer 1: 直接爬公司官網
Layer 2: Pattern 猜測 + SMTP 驗活
Layer 3: Google Dork + WHOIS
"""

import re
import asyncio
import socket
import smtplib
import dns.resolver
import httpx
import time
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from logger import add_log

# ─────────────────────────────────────────
# 常見信箱前綴（採購 > 負責人 > 通用）
# ─────────────────────────────────────────
PROCUREMENT_PREFIXES = [
    "procurement", "purchasing", "buyer", "supply", "sourcing"
]
OWNER_PREFIXES = [
    "ceo", "owner", "founder", "president", "gm", "director", "md"
]
GENERAL_PREFIXES = [
    "info", "contact", "hello", "sales", "business", "office", "admin"
]

EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)

# 過濾掉無效的假email
BLACKLIST_DOMAINS = {
    "example.com", "test.com", "sentry.io", "googleapis.com",
    "w3.org", "schema.org", "cloudflare.com", "jquery.com"
}
BLACKLIST_PREFIXES = {
    "noreply", "no-reply", "donotreply", "bounce", "mailer-daemon"
}

# ══════════════════════════════════════════
# Layer 1: 直接爬公司官網
# ══════════════════════════════════════════

CONTACT_PAGE_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/reach-us", "/get-in-touch", "/team", "/our-team",
    "/company/contact", "/pages/contact"
]

async def scrape_website_emails(domain: str) -> List[Dict]:
    """從公司官網直接爬取 email（首頁 + 聯絡頁）"""
    found_emails = []
    base_url = f"https://{domain}"
    
    pages_to_try = [base_url] + [base_url + path for path in CONTACT_PAGE_PATHS]
    
    async with httpx.AsyncClient(
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}
    ) as client:
        for url in pages_to_try[:5]:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                
                html = resp.text
                soup = BeautifulSoup(html, "lxml")
                
                # 方法1: 找 <a href="mailto:...">
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    if href.startswith("mailto:"):
                        email = href.replace("mailto:", "").split("?")[0].strip().lower()
                        if is_valid_email(email):
                            role = classify_email_role(email)
                            found_emails.append({
                                "email": email,
                                "role": role,
                                "source": "mailto_tag",
                                "confidence": 95
                            })
                
                # 方法2: Regex 掃全頁 HTML
                raw_emails = EMAIL_REGEX.findall(html)
                for email in raw_emails:
                    email = email.lower().strip(".")
                    if is_valid_email(email) and email not in [e["email"] for e in found_emails]:
                        role = classify_email_role(email)
                        found_emails.append({
                            "email": email,
                            "role": role,
                            "source": "regex_html",
                            "confidence": 80
                        })
                
                # 找到採購/負責人就提早結束
                if any(e["role"] in ["procurement", "owner"] for e in found_emails):
                    break
                
                await asyncio.sleep(1)
                
            except Exception:
                continue
    
    return deduplicate_emails(found_emails)


# ══════════════════════════════════════════
# Layer 2: Pattern 猜測 + SMTP 驗活
# ══════════════════════════════════════════

async def guess_and_verify_emails(domain: str) -> List[Dict]:
    """生成常見信箱Pattern，用SMTP RCPT TO驗證"""
    if not check_mx_record(domain):
        return []
    
    candidates = []
    
    # 採購角色優先
    for prefix in PROCUREMENT_PREFIXES[:3] + OWNER_PREFIXES[:3] + GENERAL_PREFIXES[:3]:
        candidates.append(f"{prefix}@{domain}")
    
    verified = []
    for email in candidates:
        result = smtp_verify(email, domain)
        if result["valid"]:
            role = classify_email_role(email)
            verified.append({
                "email": email,
                "role": role,
                "source": "smtp_verified_pattern",
                "confidence": 85
            })
            add_log(f"  ✅ SMTP驗活: {email} [{role}]")
        
        await asyncio.sleep(0.5)
    
    return verified


def check_mx_record(domain: str) -> bool:
    """檢查域名是否有 MX 記錄"""
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except Exception:
        return False


def smtp_verify(email: str, domain: str) -> Dict:
    """SMTP RCPT TO 驗活（不實際發信）"""
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
        
        with smtplib.SMTP(mx_host, 25, timeout=8) as smtp:
            smtp.ehlo("gmail.com")
            code, _ = smtp.rcpt(email)
            return {"valid": code == 250, "catch_all": False}
    
    except smtplib.SMTPRecipientsRefused:
        return {"valid": False, "catch_all": False}
    except Exception:
        return {"valid": False, "catch_all": None}


# ══════════════════════════════════════════
# Layer 3: Google Dork + WHOIS
# ══════════════════════════════════════════

async def google_dork_email(company_name: str, domain: str) -> List[Dict]:
    """用 Google 搜尋公司信箱"""
    found = []
    queries = [
        f'"{domain}" email procurement OR purchasing',
        f'site:{domain} "@{domain}"',
    ]
    
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        ]),
    }
    
    async with httpx.AsyncClient(timeout=12, headers=headers) as client:
        for q in queries:
            try:
                resp = await client.get(
                    "https://www.google.com/search",
                    params={"q": q, "num": 10}
                )
                if resp.status_code == 429:
                    add_log("  ⚠️ Google Rate Limit，跳過")
                    break
                
                raw_emails = EMAIL_REGEX.findall(resp.text)
                for email in raw_emails:
                    email = email.lower().strip(".")
                    if domain in email and is_valid_email(email):
                        role = classify_email_role(email)
                        found.append({
                            "email": email,
                            "role": role,
                            "source": "google_dork",
                            "confidence": 70
                        })
                
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception:
                continue
    
    return deduplicate_emails(found)


# ══════════════════════════════════════════
# 主入口：串接三層策略
# ══════════════════════════════════════════

async def find_emails_free(company_name: str, website_url: str = None) -> Dict:
    """
    免費三層 Email 發現策略
    優先級：procurement > owner/CEO > manager > general
    """
    domain = extract_domain(website_url)
    
    if not domain:
        domain = await auto_discover_domain(company_name)
    
    if not domain:
        add_log(f"  ❌ 無法找到 {company_name[:20]} 的域名")
        return {"emails": [], "domain": None, "mx_valid": False, "contacts": []}
    
    add_log(f"  🌐 域名: {domain}")
    all_contacts = []
    
    # Layer 1: 直接爬官網
    add_log(f"  🕷️ Layer1: 爬官網...")
    website_results = await scrape_website_emails(domain)
    all_contacts.extend(website_results)
    add_log(f"    → {len(website_results)} 筆")
    
    if _has_priority_contact(all_contacts):
        return _build_result(domain, all_contacts)
    
    # Layer 2: Pattern + SMTP 驗活
    add_log(f"  🔐 Layer2: SMTP驗活...")
    smtp_results = await guess_and_verify_emails(domain)
    all_contacts.extend(smtp_results)
    add_log(f"    → {len(smtp_results)} 筆")
    
    if _has_priority_contact(all_contacts):
        return _build_result(domain, all_contacts)
    
    # Layer 3: Google Dork
    add_log(f"  🔎 Layer3: Google Dork...")
    dork_results = await google_dork_email(company_name, domain)
    all_contacts.extend(dork_results)
    add_log(f"    → {len(dork_results)} 筆")
    
    return _build_result(domain, all_contacts)


async def auto_discover_domain(company_name: str) -> Optional[str]:
    """從公司名自動猜域名"""
    clean = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())[:20]
    suffixes = [".com", ".co", ".net", ".org", ".io"]
    
    async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
        for suffix in suffixes:
            domain = clean + suffix
            try:
                resp = await client.head(f"https://{domain}")
                if resp.status_code < 400:
                    return domain
            except Exception:
                continue
    return None


# ══════════════════════════════════════════
# 輔助函數
# ══════════════════════════════════════════

ROLE_KEYWORDS = {
    "procurement": PROCUREMENT_PREFIXES,
    "owner": OWNER_PREFIXES,
    "sales": ["sales", "biz", "business", "bd"],
    "general": GENERAL_PREFIXES,
}

def classify_email_role(email: str) -> str:
    prefix = email.split("@")[0].lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(k in prefix for k in keywords):
            return role
    return "unknown"

def is_valid_email(email: str) -> bool:
    if not EMAIL_REGEX.match(email):
        return False
    domain = email.split("@")[-1]
    prefix = email.split("@")[0].lower()
    if domain in BLACKLIST_DOMAINS:
        return False
    if any(b in prefix for b in BLACKLIST_PREFIXES):
        return False
    if len(email) > 100 or "." not in domain:
        return False
    return True

def deduplicate_emails(contacts: List[Dict]) -> List[Dict]:
    seen = set()
    result = []
    for c in contacts:
        if c["email"] not in seen:
            seen.add(c["email"])
            result.append(c)
    return result

def extract_domain(url: str) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.replace("www.", "") or None

ROLE_PRIORITY = {"procurement": 4, "owner": 3, "sales": 2, "general": 1, "unknown": 0}

def _has_priority_contact(contacts: List[Dict]) -> bool:
    return any(c["role"] in ("procurement", "owner") for c in contacts)

def _build_result(domain: str, contacts: List[Dict]) -> Dict:
    deduped = deduplicate_emails(contacts)
    sorted_contacts = sorted(
        deduped,
        key=lambda x: (ROLE_PRIORITY.get(x["role"], 0), x["confidence"]),
        reverse=True
    )
    return {
        "domain": domain,
        "mx_valid": check_mx_record(domain),
        "contacts": sorted_contacts[:5],
        "emails": [c["email"] for c in sorted_contacts[:3]],
        "primary_contact": sorted_contacts[0] if sorted_contacts else None
    }