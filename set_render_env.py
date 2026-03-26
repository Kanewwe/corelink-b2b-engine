
import requests
import json

headers = {
    "Authorization": "Bearer rnd_UrCjbEPWRxHaTfN4Agy08hW9VTLT",
    "Content-Type": "application/json"
}

def set_env_var(service_id, key, value):
    url = f"https://api.render.com/v1/services/{service_id}/env-vars"
    # Render API: PUT /v1/services/{id}/env-vars replaces all env vars
    # So I should fetch first and then add/update
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        vars = response.json()
        updated_vars = []
        found = False
        for v in vars:
            item = v['envVar']
            if item['key'] == key:
                item['value'] = value
                found = True
            updated_vars.append({"key": item['key'], "value": item['value']})
        
        if not found:
            updated_vars.append({"key": key, "value": value})
            
        # PUT to update
        put_response = requests.put(url, headers=headers, json=updated_vars)
        if put_response.status_code == 200:
            print(f"✅ Successfully set {key}={value} for {service_id}")
        else:
            print(f"❌ Failed to set {key} for {service_id}: {put_response.status_code}")
            print(put_response.text)
    else:
        print(f"❌ Failed to fetch vars for {service_id}")

services = {
    "uat": "srv-d71npcgule4c73cvnjk0",
    "prd": "srv-d71kahtactks7392rff0"
}

set_env_var(services["uat"], "APP_ENV", "uat")
set_env_var(services["prd"], "APP_ENV", "production")
