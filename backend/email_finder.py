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
    "sales@{domain}",
    "quotes@{domain}",
]

COMMON_TLDS = ["com", "org", "net", "io", "co", "biz", "us"]


def guess_domain_from_name(company_name: str) -> Optional[str]:
    """Try common TLDs based on cleaned company name."""
    # Strip common suffixes
    clean = re.sub(
        r'\s+(Inc|LLC|Corp|Ltd|Manufacturing|Mfg|Co|Inc\.|Company|Industries|Industrial|Solutions|Services|Group|Holdings|Enterprises|Inc)$',
        '',
        company_name,
        flags=re.IGNORECASE
    )
    # Remove extra whitespace and special chars
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', clean)
    clean = ' '.join(clean.split())  # normalize whitespace
    # Create slug - remove spaces, 'the', etc.
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


# Blocklist of domains that are not company domains
BLOCKED_DOMAINS = {
    'w3.org', 'wikipedia.org', 'facebook.com', 'twitter.com', 'linkedin.com',
    'youtube.com', 'instagram.com', 'pinterest.com', 'reddit.com', 'amazon.com',
    'google.com', 'bing.com', 'yahoo.com', 'microsoft.com', 'apple.com',
    'github.com', 'stackoverflow.com', 'www.bing.com', 'www.google.com',
    'duckduckgo.com', 'html.duckduckgo.com', 'yelp.com', 'yellowpages.com',
    'superpages.com', 'bbb.org', 'crunchbase.com', 'bloomberg.com',
    'en.wikipedia.org', 'en-us.facebook.com', 'support.google.com',
    'zhihu.com', 'imdb.com', 'atwiki.jp', 'tiktok.com', 'baidu.com',
    'qq.com', 'weibo.com', 'alibaba.com', 'aliexpress.com', 'wix.com',
    'squarespace.com', 'shopify.com', 'wordpress.com', 'godaddy.com',
    'indeed.com', 'glassdoor.com', ' manta.com', 'houzz.com',
    'homify.com', 'architecturaldigest.com', 'houzz.com', 'mapquest.com',
    'ask.com', 'aol.com', 'ask.com'
}

# Blocked patterns
BLOCKED_PATTERNS = [
    'bing.com', 'google.com', 'yahoo.com', 'duckduckgo', 'facebook.com',
    'twitter.com', 'linkedin.com', 'youtube.com', 'instagram.com',
    'wikipedia.org', 'w3.org', 'amazon.com', 'microsoft.com', 'apple.com',
    'support.google', 'help.google', 'policies.google', 'zhihu.com',
    'imdb.com', 'atwiki.jp', 'tiktok.com', 'baidu.com', 'qq.com',
    'weibo.com', 'alibaba.com', 'aliexpress.com', 'wix.com',
    'squarespace.com', 'shopify.com', 'wordpress.com', 'godaddy.com',
    'indeed.com', 'glassdoor.com', 'manta.com', 'houzz.com',
    'homify.com', 'architecturaldigest.com', 'mapquest.com',
    'ask.com', 'aol.com', 'pinterest.com', 'reddit.com',
    'yelp.com', 'yellowpages.com', 'bbb.org', 'crunchbase.com',
    'stackoverflow.com', 'github.com'
]


def is_valid_company_domain(domain: str) -> bool:
    """Check if domain is a valid company domain (not a known platform/redirect)."""
    if not domain:
        return False
    domain_lower = domain.lower()
    
    # Block exact matches
    if domain_lower in BLOCKED_DOMAINS:
        return False
    
    # Block domains that contain blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in domain_lower:
            return False
    
    # Domain should be reasonably short (company sites are usually not too long)
    if len(domain_lower) > 40:
        return False
        
    return True


async def find_domain_via_search(company_name: str) -> Optional[str]:
    """Search for company domain via DuckDuckGo."""
    # Clean company name for search
    clean_name = re.sub(r'\s+(Inc|LLC|Corp|Ltd|Company)$', '', company_name, flags=re.IGNORECASE)
    query = f"{clean_name} official website .com"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        try:
            # Use DuckDuckGo HTML
            r = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers
            )
            if r.status_code == 200:
                import bs4
                soup = bs4.BeautifulSoup(r.text, 'html.parser')
                
                # DuckDuckGo HTML results have result links with URLs
                for a_tag in soup.find_all('a', class_='result__a'):
                    href = a_tag.get('href', '')
                    if href and 'http' in href:
                        # Extract domain from URL
                        m = re.search(r'https?://(?:www\.)?([^/?]+)', href)
                        if m:
                            domain = m.group(1).lower()
                            # Verify it's valid before returning
                            if is_valid_company_domain(domain) and domain_exists(domain):
                                return domain
                                
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        # Fallback: try direct domain guess with variations
        # Try common patterns like companynameinc.com, companynamellc.com
        base = re.sub(r'[^a-zA-Z0-9]', '', clean_name).lower()
        for suffix in ['inc', 'llc', 'corp', 'company']:
            candidate = f"{base}{suffix}.com"
            if is_valid_company_domain(candidate) and domain_exists(candidate):
                return candidate
        
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
