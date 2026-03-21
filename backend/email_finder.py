"""
Email discovery via DNS MX record validation.
Finds company domain and generates email candidates.
"""

import re
import socket
import asyncio
from typing import Optional, List
import dns.resolver
import httpx

COMMON_EMAIL_PATTERNS = [
    "info@{domain}",
    "contact@{domain}",
    "sales@{domain}",
    "hello@{domain}",
    "support@{domain}",
]

COMMON_TLDS = ["com", "org", "net", "io", "co", "biz", "industries"]


def guess_domain_from_name(company_name: str) -> Optional[str]:
    """Try common TLDs based on cleaned company name."""
    # Strip common suffixes
    clean = re.sub(
        r'\s+(Inc|LLC|Corp|Ltd|Manufacturing|Mfg|Co|Inc\.|Company|Industries|Industrial|Solutions|Services|Group|Holdings|Enterprises)$',
        '',
        company_name,
        flags=re.IGNORECASE
    )
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', clean)
    slug = clean.lower().replace(' ', '').replace('the', '')
    
    for tld in COMMON_TLDS:
        candidate = f"{slug}.{tld}"
        if domain_exists(candidate):
            return candidate
    return None


def domain_exists(domain: str) -> bool:
    """Check if domain resolves via DNS."""
    try:
        socket.getaddrinfo(domain, 80)
        return True
    except (socket.gaierror, socket.timeout, OSError):
        return False


async def find_domain_via_search(company_name: str) -> Optional[str]:
    """Search for company domain via Bing/DuckDuckGo."""
    query = f"{company_name} manufacturer"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Bot/0.1)"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        # Try Bing
        try:
            r = await client.get(
                "https://www.bing.com/search",
                params={"q": query, "mkt": "en-US"},
                headers=headers
            )
            if r.status_code == 200:
                domains = re.findall(r'https?://(?!www\.bing|microsoft|linkedin|facebook|youtube|twitter)[^\s"\'<>]+', r.text)
                for d in domains:
                    d = d.rstrip('/')
                    m = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)', d)
                    if m:
                        domain = m.group(1)
                        if domain_exists(domain):
                            return domain
        except Exception:
            pass
        
        # Try DuckDuckGo HTML
        try:
            r = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers
            )
            if r.status_code == 200:
                domains = re.findall(r'https?://(?!duckduckgo)[^\s"\'<>]+', r.text)
                for d in domains:
                    d = d.rstrip('/')
                    m = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})', d)
                    if m:
                        domain = m.group(1)
                        if domain_exists(domain):
                            return domain
        except Exception:
            pass

    return None


def check_mx_record(domain: str) -> bool:
    """Return True if domain has valid MX records."""
    try:
        records = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(records) > 0
    except Exception:
        return False


def generate_email_candidates(domain: str) -> List[str]:
    return [p.format(domain=domain) for p in COMMON_EMAIL_PATTERNS]


async def find_emails_for_company(company_name: str) -> dict:
    """
    Main entry point: find domain, check MX, generate email candidates.
    Returns: {"domain": str, "mx_valid": bool, "emails": list}
    """
    # Step 1: Guess domain from name
    domain = guess_domain_from_name(company_name)
    
    # Step 2: Search if guess failed
    if not domain:
        domain = await find_domain_via_search(company_name)

    if not domain:
        return {"domain": None, "mx_valid": False, "emails": []}

    # Step 3: Check MX
    mx_valid = check_mx_record(domain)
    
    emails = []
    if mx_valid:
        emails = generate_email_candidates(domain)

    return {
        "domain": domain,
        "mx_valid": mx_valid,
        "emails": emails
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 email_finder.py \"Company Name\"")
        sys.exit(1)
    
    company = " ".join(sys.argv[1:])
    result = asyncio.run(find_emails_for_company(company))
    print(f"Company: {company}")
    print(f"Domain: {result['domain']}")
    print(f"MX Valid: {result['mx_valid']}")
    print(f"Emails: {result['emails']}")
