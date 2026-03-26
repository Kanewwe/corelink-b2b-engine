
import requests
import json

headers = {"Authorization": "Bearer rnd_UrCjbEPWRxHaTfN4Agy08hW9VTLT"}

def get_env_vars(service_id):
    url = f"https://api.render.com/v1/services/{service_id}/env-vars"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

services = {
    "uat": "srv-d71npcgule4c73cvnjk0",
    "prd": "srv-d71kahtactks7392rff0"
}

for name, sid in services.items():
    print(f"\n--- {name} ({sid}) ---")
    vars = get_env_vars(sid)
    if vars:
        for v in vars:
            print(f"{v['envVar']['key']} = {v['envVar']['value']}")
    else:
        print("Failed to fetch vars")
