
import requests
import json

headers = {"Authorization": "Bearer rnd_UrCjbEPWRxHaTfN4Agy08hW9VTLT"}
url = "https://api.render.com/v1/services"

response = requests.get(url, headers=headers)
if response.status_code == 200:
    services = response.json()
    print(json.dumps(services, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
