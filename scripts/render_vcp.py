import requests
import time
import sys
import os

# Render Configuration
RENDER_API_KEY = "rnd_TFrozA3dFkCYkDteXv8sNEwDcYVt"
BACKEND_SERVICE_ID = "srv-d71npcgule4c73cvnjk0"
FRONTEND_SERVICE_ID = "srv-d71nptua2pns73fauhg0"
UAT_URL = "https://linkora-backend-uat.onrender.com"

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_latest_deploy(service_id):
    url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=1"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        deploys = resp.json()
        if deploys:
            return deploys[0]["deploy"]
    return None

def wait_for_deploy(service_id, name):
    print(f"📡 [Render] Monitoring deployment for {name}...")
    start_time = time.time()
    last_status = None
    
    while True:
        deploy = get_latest_deploy(service_id)
        if not deploy:
            print("⚠️ No deployment found.")
            break
            
        status = deploy["status"]
        if status != last_status:
            print(f"🕒 [{name}] Status: {status}")
            last_status = status
            
        if status == "live":
            print(f"✅ [{name}] Deployment is LIVE!")
            return True
        elif status in ["build_failed", "update_failed", "canceled"]:
            print(f"❌ [{name}] Deployment FAILED with status: {status}")
            return False
            
        # Timeout after 10 minutes
        if time.time() - start_time > 600:
            print(f"⏰ [{name}] Deployment timed out.")
            return False
            
        time.sleep(15)

def verify_health():
    print(f"🔍 [UAT] Verifying health at {UAT_URL}/api/health...")
    try:
        resp = requests.get(f"{UAT_URL}/api/health", timeout=10)
        if resp.status_code == 200:
            print(f"✅ [Health] Backend is responding: {resp.json()}")
            return True
        else:
            print(f"⚠️ [Health] Unexpected status: {resp.status_code}")
    except Exception as e:
        print(f"❌ [Health] Connection error: {e}")
    return False

if __name__ == "__main__":
    print("🚀 Linkora V3.4/V3.5 Automated Deployment Checker")
    print("-" * 50)
    
    # Check Backend
    if wait_for_deploy(BACKEND_SERVICE_ID, "Backend-UAT"):
        verify_health()
    
    # Check Frontend
    wait_for_deploy(FRONTEND_SERVICE_ID, "Frontend-UAT")
    
    print("-" * 50)
    print("🏁 Automation Check Complete.")
