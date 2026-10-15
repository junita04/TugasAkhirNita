import requests
import sys

try:
    response = requests.get("https://api.github.com/repos/minio/mc/releases/latest", timeout=10)
    data = response.json()
    assets = [a for a in data['assets'] if 'mc_linux_amd64' in a['name']]
    if assets:
        print(assets[0]['browser_download_url'])
    else:
        print("NOT FOUND")
except Exception as e:
    print(f"ERROR: {e}")