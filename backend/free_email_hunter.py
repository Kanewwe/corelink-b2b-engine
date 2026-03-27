"""
免費 Email 發現系統 - 三層策略 v2
修正清單：
 - EMAIL_REGEX 轉義修正
 - SMTP 改用 port 587 / 465 fallback
 - Google Dork 換成 Google Custom Search API（免費100次/日）
 - auto_discover_domain 改用 Google 搜尋輔助
 - 加入整體 timeout 保護
 - 加入 catch-all 偵測防止誤判
 - User-Agent 改為真實瀏覽器
"""

import re
import asyncio
import smtplib
import ssl
import dns.resolver
import httpx
import time
import random
import os
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from logger import add_log

# ─────────────────────────────────────────
# 設定（從環境變數讀取）
# ─────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_CSE_ID", "")

# ─────────────────────────────────────────
# 常見信箱前綴（採購 > 負責人 > 通用）
# ─────────────────────────────────────────
PROCUREMENT_PREFIXES = [
    "procurement", "purchasing", "buyer", "supply", "sourcing",
    "purchase", "supply-chain", "vendor"
]
OWNER_PREFIXES = [
    "ceo", "owner", "founder", "president", "gm", "director", "md",
    "manager", "vp", "head", "chief"
]
GENERAL_PREFIXES = [
    "info", "contact", "hello", "sales", "business", "office", "admin",
    "inquiry", "enquiry", "support", "export", "international"
]

# ✅ 修正：移除多餘的雙重反斜線
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)

BLACKLIST_DOMAINS = {
    "example.com", "test.com", "sentry.io", "googleapis.com",
    "w3.org", "schema.org", "cloudflare.com", "jquery.com",
    "wix.com", "wordpress.com", "squarespace.com",
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com"
}
BLACKLIST_PREFIXES = {
    "noreply", "no-reply", "donotreply", "bounce",
    "mailer-daemon", "postmaster", "abuse", "spam"
}

# ✅ 新增：真實瀏覽器 UA 輪換
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# ══════════════════════════════════════════
# Layer 1: 直接爬公司官網
# ══════════════════════════════════════════

CONTACT_PAGE_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/reach-us", "/get-in-touch", "/team", "/our-team",
    "/company/contact", "/pages/contact",
    "/en/contact", "/us/contact",
]

async def scrape_website_emails(domain: str) -> List[Dict]:
    """從公司官網直接爬取 email（首頁 + 聯絡頁）"""
    found_emails = []
    base_url = f"https://{domain}"
    pages_to_try = [base_url] + [base_url + path for path in CONTACT_PAGE_PATHS]

    async with httpx.AsyncClient(
        timeout=10,
        follow_redirects=True,
        headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    ) as client:
        for url in pages_to_try[:6]:
            try:
                resp = await client.get(url)
                if resp.status_code == 404:
                    continue
                if resp.status_code != 200:
                    continue

                html = resp.text
                soup = BeautifulSoup(html, "lxml")

                # 方法1: <a href="mailto:...">
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

                # 方法2: Regex 掃全頁
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

                # 方法3: 掃 <meta> 標籤
                for meta in soup.find_all("meta"):
                    content = meta.get("content", "")
                    meta_emails = EMAIL_REGEX.findall(content)
                    for email in meta_emails:
                        email = email.lower().strip(".")
                        if is_valid_email(email) and email not in [e["email"] for e in found_emails]:
                            found_emails.append({
                                "email": email,
                                "role": classify_email_role(email),
                                "source": "meta_tag",
                                "confidence": 85
                            })

                if _has_priority_contact(found_emails):
                    break

                await asyncio.sleep(random.uniform(0.8, 1.5))

            except (httpx.ConnectError, httpx.TimeoutException):
                continue
            except Exception:
                continue

    return deduplicate_emails(found_emails)


# ══════════════════════════════════════════
# Layer 2: Pattern 猜測 + SMTP 驗活
# ══════════════════════════════════════════

async def guess_and_verify_emails(domain: str) -> List[Dict]:
    """生成常見信箱 Pattern，用 SMTP 驗活"""
    if not check_mx_record(domain):
        add_log(f"⚠️ {domain} 無 MX 記錄，跳過 Layer 2")
        return []

    # ✅ 新增：catch-all 偵測
    fake_test = f"zzz_nonexist_test_xyz_{random.randint(1000,9999)}@{domain}"
    fake_result = smtp_verify(fake_test, domain)
    is_catch_all = fake_result.get("valid", False)

    if is_catch_all:
        add_log(f"⚠️ {domain} 為 catch-all server，SMTP 驗活結果不可信，跳過 Layer 2")
        return []

    candidates = (
        PROCUREMENT_PREFIXES[:5] +
        OWNER_PREFIXES[:4] +
        GENERAL_PREFIXES[:5]
    )

    verified = []
    for prefix in candidates:
        email = f"{prefix}@{domain}"
        result = smtp_verify(email, domain)
        if result.get("valid"):
            role = classify_email_role(email)
            verified.append({
                "email": email,
                "role": role,
                "source": "smtp_verified_pattern",
                "confidence": 85
            })
            add_log(f"✅ SMTP驗活: {email} [{role}]")

        if role in ("procurement", "owner"):
            break

        await asyncio.sleep(random.uniform(0.3, 0.7))

    return verified


def check_mx_record(domain: str) -> bool:
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except Exception:
        return False


def smtp_verify(email: str, domain: str) -> Dict:
    """
    ✅ 修正：改用 port 587 (STARTTLS) 為主，port 465 (SSL) 為 fallback
    Render / AWS / GCP 封鎖 port 25，必須改用 587
    """
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(
            sorted(mx_records, key=lambda r: r.preference)[0].exchange
        ).rstrip(".")
    except Exception:
        return {"valid": False, "catch_all": None}

    # ✅ 嘗試順序：587 (STARTTLS) → 465 (SSL) → 25 (最後手段)
    attempts = [
        ("587_starttls", lambda: _smtp_verify_587(mx_host, email)),
        ("465_ssl", lambda: _smtp_verify_465(mx_host, email)),
        ("25_plain", lambda: _smtp_verify_25(mx_host, email)),
    ]

    for method_name, fn in attempts:
        try:
            result = fn()
            if result is not None:
                return {"valid": result, "catch_all": False, "method": method_name}
        except Exception:
            continue

    return {"valid": False, "catch_all": None}


def _smtp_verify_587(mx_host: str, email: str) -> Optional[bool]:
    with smtplib.SMTP(mx_host, 587, timeout=8) as smtp:
        smtp.ehlo("outreach.local")
        smtp.starttls()
        smtp.ehlo("outreach.local")
        smtp.mail("verify@outreach.local")
        code, _ = smtp.rcpt(email)
        return code == 250


def _smtp_verify_465(mx_host: str, email: str) -> Optional[bool]:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(mx_host, 465, timeout=8, context=context) as smtp:
        smtp.ehlo("outreach.local")
        smtp.mail("verify@outreach.local")
        code, _ = smtp.rcpt(email)
        return code == 250


def _smtp_verify_25(mx_host: str, email: str) -> Optional[bool]:
    with smtplib.SMTP(mx_host, 25, timeout=8) as smtp:
        smtp.ehlo("outreach.local")
        smtp.mail("verify@outreach.local")
        code, _ = smtp.rcpt(email)
        return code == 250


# ══════════════════════════════════════════
# Layer 3: Google Custom Search API
# ══════════════════════════════════════════

async def google_search_emails(domain: str) -> List[Dict]:
    """
    ✅ 修正：改用 Google Custom Search API（免費 100 次/日）
    拋棄直接打 google.com/search 的方式
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        add_log("⚠️ 未設定 GOOGLE_API_KEY 或 GOOGLE_CSE_ID，跳過 Layer 3")
        return []

    emails = []
    
    # 查詢語法：找網站內的 email 地址
    queries = [
        f'site:{domain} "@{domain}"',
        f'site:{domain} email OR contact OR procurement',
    ]

    for query in queries:
        try:
            results = await _google_cse_search(query)
            for item in results:
                found_emails = EMAIL_REGEX.findall(item.get("snippet", ""))
                for email in found_emails:
                    email = email.lower()
                    if is_valid_email(email):
                        emails.append({
                            "email": email,
                            "role": classify_email_role(email),
                            "source": "google_cse",
                            "confidence": 75
                        })
            
            await asyncio.sleep(1)  # API 速率限制
            
        except Exception as e:
            add_log(f"⚠️ Google CSE 搜尋失敗: {e}")
            continue

    return deduplicate_emails(emails)


async def _google_cse_search(query: str) -> List[Dict]:
    """呼叫 Google Custom Search API"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_SEARCH_ENGINE_ID,
        "q": query,
        "num": 10,
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", [])
        else:
            add_log(f"⚠️ Google CSE API 錯誤: {resp.status_code}")
            return []


# ══════════════════════════════════════════
# Domain 自動發現（改良版）
# ══════════════════════════════════════════

async def auto_discover_domain(company_name: str) -> Optional[str]:
    """
    ✅ 修正：用 Google 搜尋輔助猜測 domain
    從搜尋結果找出官方網站，而非直接用公司名猜測
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        # Fallback：簡單的公司名處理
        return _simple_domain_guess(company_name)
    
    try:
        # 搜尋 "公司名 官網" 或 "公司名 official website"
        query = f'"{company_name}" official website'
        results = await _google_cse_search(query)
        
        for item in results:
            link = item.get("link", "")
            domain = _extract_domain(link)
            if domain and _is_likely_official(domain, company_name):
                add_log(f"🔍 自動發現 domain: {domain}")
                return domain
        
        # 找不到就用簡單猜測
        return _simple_domain_guess(company_name)
        
    except Exception as e:
        add_log(f"⚠️ Domain 自動發現失敗: {e}")
        return _simple_domain_guess(company_name)


def _simple_domain_guess(company_name: str) -> Optional[str]:
    """簡單的公司名到 domain 猜測"""
    # 移除常見後綴
    clean_name = company_name
    for suffix in [" Inc", " LLC", " Corp", " Ltd", " Co.", " Co", " Inc.", " LLC.", " Corp."]:
        clean_name = clean_name.replace(suffix, "")
    
    # 移除特殊字符
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', clean_name)
    
    # 轉換為 domain 格式
    domain = clean_name.lower().replace(" ", "") + ".com"
    
    # 基本驗證
    if len(domain) < 6:
        return None
    
    return domain


def _extract_domain(url: str) -> Optional[str]:
    """從 URL 提取 domain"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return None


def _is_likely_official(domain: str, company_name: str) -> bool:
    """判斷是否為官方網站"""
    # 排除明顯不是官方網站的 domain
    exclude_domains = [
        "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
        "youtube.com", "wikipedia.org", "yelp.com", "yellowpages.com",
        "glassdoor.com", "indeed.com", "crunchbase.com", "bloomberg.com"
    ]
    
    for exclude in exclude_domains:
        if exclude in domain:
            return False
    
    return True


# ══════════════════════════════════════════
# 輔助函數
# ══════════════════════════════════════════

def is_valid_email(email: str) -> bool:
    """驗證 email 是否有效"""
    if not email or "@" not in email:
        return False
    
    local, domain = email.rsplit("@", 1)
    
    # 檢查長度
    if len(local) > 64 or len(domain) > 255:
        return False
    
    # 檢查黑名單
    if domain in BLACKLIST_DOMAINS:
        return False
    
    # 檢查前綴黑名單
    if local.split("+")[0].lower() in BLACKLIST_PREFIXES:
        return False
    
    # 檢查 domain 格式
    if not re.match(r'^[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', domain):
        return False
    
    return True


def classify_email_role(email: str) -> str:
    """分類 email 角色"""
    local = email.split("@")[0].lower()
    
    for prefix in PROCUREMENT_PREFIXES:
        if local.startswith(prefix):
            return "procurement"
    
    for prefix in OWNER_PREFIXES:
        if local.startswith(prefix):
            return "owner"
    
    return "general"


def _has_priority_contact(emails: List[Dict]) -> bool:
    """檢查是否已找到優先級聯絡人"""
    for email in emails:
        if email.get("role") in ("procurement", "owner"):
            return True
    return False


def deduplicate_emails(emails: List[Dict]) -> List[Dict]:
    """去除重複的 email"""
    seen = set()
    result = []
    for email in emails:
        e = email["email"].lower()
        if e not in seen:
            seen.add(e)
            result.append(email)
    return result


# ══════════════════════════════════════════
# 主程式：整合三層策略
# ══════════════════════════════════════════

async def find_emails_free(domain: str, company_name: str = "", timeout: int = 30) -> Dict:
    """
    整合三層 email 發現策略
    ✅ 新增：整體 timeout 保護（最多 30 秒）
    """
    start_time = time.time()
    overall_timeout = timeout  # 可外部控制，避免 worker timeout
    
    result = {
        "domain": domain,
        "emails": [],
        "sources": {},
        "best_email": None,
        "confidence": 0
    }
    
    try:
        # Layer 1: 直接爬官網（最高優先）
        add_log(f"🔍 Layer 1: 爬取官網 {domain}")
        layer1_emails = await scrape_website_emails(domain)
        
        for email in layer1_emails:
            result["emails"].append(email)
            result["sources"][email["email"]] = "website"
        
        if layer1_emails:
            add_log(f"✅ Layer 1 完成，找到 {len(layer1_emails)} 個 email")
        
        # 如果找到採購/老闆，直接結束
        if _has_priority_contact(layer1_emails):
            result["best_email"] = _select_best_email(result["emails"])
            return result
        
        # 檢查 timeout
        if time.time() - start_time > overall_timeout:
            add_log("⏰ 整體 timeout，結束")
            return result
        
        # Layer 2: SMTP 驗活
        add_log(f"🔍 Layer 2: SMTP 驗活 {domain}")
        layer2_emails = await guess_and_verify_emails(domain)
        
        for email in layer2_emails:
            result["emails"].append(email)
            result["sources"][email["email"]] = "smtp"
        
        if layer2_emails:
            add_log(f"✅ Layer 2 完成，找到 {len(layer2_emails)} 個 email")
        
        # 如果找到採購/老闆，直接結束
        if _has_priority_contact(layer2_emails):
            result["best_email"] = _select_best_email(result["emails"])
            return result
        
        # 檢查 timeout
        if time.time() - start_time > overall_timeout:
            add_log("⏰ 整體 timeout，結束")
            return result
        
        # Layer 3: Google 搜尋
        if GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
            add_log(f"🔍 Layer 3: Google 搜尋 {domain}")
            layer3_emails = await google_search_emails(domain)
            
            for email in layer3_emails:
                result["emails"].append(email)
                result["sources"][email["email"]] = "google"
            
            if layer3_emails:
                add_log(f"✅ Layer 3 完成，找到 {len(layer3_emails)} 個 email")
        
    except asyncio.TimeoutError:
        add_log("⏰ 非同步任務 timeout")
    except Exception as e:
        add_log(f"❌ Email 發現錯誤: {e}")
    
    # 去除重複並選擇最佳
    result["emails"] = deduplicate_emails(result["emails"])
    result["best_email"] = _select_best_email(result["emails"])
    
    elapsed = time.time() - start_time
    add_log(f"🏁 Email 發現完成，共 {len(result['emails'])} 個，耗时 {elapsed:.1f}s")
    
    return result


def _select_best_email(emails: List[Dict]) -> Optional[Dict]:
    """選擇最佳 email"""
    if not emails:
        return None
    
    # 按角色優先級排序
    role_priority = {"procurement": 0, "owner": 1, "general": 2}
    
    # 按 confidence 排序
    sorted_emails = sorted(
        emails,
        key=lambda e: (role_priority.get(e.get("role", ""), 3), -e.get("confidence", 0))
    )
    
    return sorted_emails[0] if sorted_emails else None


# ══════════════════════════════════════════
# 入口點
# ══════════════════════════════════════════

if __name__ == "__main__":
    async def test():
        domain = "apple.com"
        result = await find_emails_free(domain)
        print(f"\n結果: {result}")
    
    asyncio.run(test())
