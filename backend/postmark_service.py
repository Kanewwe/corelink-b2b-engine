from postmark import PostmarkClient
import logging

logger = logging.getLogger(__name__)

def get_postmark_client(api_token: str):
    """Initialize Postmark client"""
    return PostmarkClient(server_token=api_token)

def send_postmark_email(api_token: str, from_email: str, to_email: str, subject: str, html_body: str, message_stream: str = "outbound"):
    """
    Send email via Postmark SDK
    v3.5 Implementation
    """
    client = get_postmark_client(api_token)
    try:
        # Note: Postmark Python SDK structure
        client.emails.send(
            From=from_email,
            To=to_email,
            Subject=subject,
            HtmlBody=html_body,
            MessageStream=message_stream
        )
        return True, "Sent successfully via Postmark"
    except Exception as e:
        logger.error(f"Postmark Send Error: {e}")
        return False, str(e)

def verify_postmark_token(api_token: str):
    """
    Verify API Token by fetching server details.
    Used in Step 1 of the Config Wizard.
    """
    client = get_postmark_client(api_token)
    try:
        server = client.servers.get()
        return True, server.get("Name", "Postmark Server")
    except Exception as e:
        return False, str(e)

def get_domain_verification_status(api_token: str, domain: str):
    """
    Check DNS/Domain verification status for SPF/DKIM.
    Used in Step 3 of the Config Wizard.
    """
    client = get_postmark_client(api_token)
    try:
        # This is a hypothetical call based on Postmark API, 
        # normally you list signatures or get a specific domain signature.
        domains = client.domains.list()
        # Find the domain in the list
        for d in domains:
            if d.get("Name") == domain:
                return {
                    "spf": d.get("SPFVerified"),
                    "dkim": d.get("DKIMVerified"),
                    "return_path": d.get("ReturnPathDomainVerified"),
                    "verified": d.get("Verified")
                }
        return None
    except Exception as e:
        logger.error(f"Postmark Domain Check Error: {e}")
        return None
