"""
Check existing charts and dashboard, then create/update as needed.
"""
import requests
import json

SUPERSET = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "change-me"

def get_jwt_token():
    r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
        "username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True
    })
    return r.json().get("access_token")

def api_get(token, path):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}{path}", headers=headers)
    return r.json()

def api_post(token, path, data):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(f"{SUPERSET}{path}", headers=headers, json=data)
    return r

def api_put(token, path, data):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.put(f"{SUPERSET}{path}", headers=headers, json=data)
    return r

def api_delete(token, path):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.delete(f"{SUPERSET}{path}", headers=headers)
    return r

token = get_jwt_token()

# Check existing dashboard
print("=== Existing Dashboard ===")
dash = api_get(token, "/api/v1/dashboard/3")
print(f"Title: {dash.get('result', {}).get('dashboard_title')}")
print(f"Slug: {dash.get('result', {}).get('slug')}")
print(f"Published: {dash.get('result', {}).get('published')}")

# Check existing charts
print("\n=== Existing Charts ===")
charts = api_get(token, "/api/v1/chart/?q=(page_size:100)")
print(f"Total charts: {charts.get('count', 0)}")
for c in charts.get("result", []):
    print(f"  ID={c['id']} Name={c.get('slice_name', 'N/A')} Type={c.get('viz_type', 'N/A')}")
