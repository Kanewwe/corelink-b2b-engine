
import requests
import json

base_url = "https://linkora-backend-uat.onrender.com"
email = "admin@linkora.com"
password = "Corelink2024!"

def verify():
    try:
        # 1. Login (OAuth2 uses form data)
        print(f"Logging in as {email}...")
        r = requests.post(f"{base_url}/api/login", data={"username": email, "password": password})
        if r.status_code != 200:
            print(f"❌ Login failed: {r.status_code}")
            print(r.text)
            return
            
        token = r.json().get("access_token")
        print("✅ Login successful.")
        
        # 2. Fetch History
        print("Fetching search history...")
        r = requests.get(f"{base_url}/api/search-history", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            history = r.json()
            print(f"✅ History Count: {len(history)}")
            if len(history) > 0:
                print(f"Sample item: {history[0]['keywords']} (Status: {history[0]['status']})")
        else:
            print(f"❌ Failed to fetch history: {r.status_code}")
            print(r.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify()
