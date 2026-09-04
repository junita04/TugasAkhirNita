import requests
import json

SUPERSET_URL = "http://superset:8088"

# Get JWT token
r = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json()["access_token"]
jwt_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Get CSRF token
r_csrf = requests.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/", headers=jwt_headers)
csrf_token = r_csrf.json().get("result", "")

# Use session-based approach with CSRF
s = requests.Session()
s.cookies.set("session", "", domain="superset")

# Login via API to get session cookie
login_resp = s.post(f"{SUPERSET_URL}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
}, headers={"Content-Type": "application/json"})
print(f"Session login: {login_resp.status_code}")

# Also set JWT in session
s.headers.update({"Authorization": f"Bearer {token}"})

# Get CSRF from HTML endpoint
csrf_resp = s.get(f"{SUPERSET_URL}/superset/csrf_token/")
print(f"HTML CSRF: {csrf_resp.status_code} len={len(csrf_resp.text)}")

# Now try creating dataset with session cookies + CSRF header
headers = {
    "X-CSRFToken": csrf_token,
    "Content-Type": "application/json",
    "Referer": f"{SUPERSET_URL}/",
}

payload = {
    "database": 1,
    "schema": "gold",
    "table_name": "dim_mahasiswa_fix",
}
resp = s.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
print(f"Create dim_mahasiswa_fix: {resp.status_code} {resp.text[:300]}")

if resp.status_code in [200, 201]:
    ds_id = resp.json().get("id")
    print(f"  Created with ID: {ds_id}")

payload["table_name"] = "fact_khs_fix"
resp = s.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
print(f"Create fact_khs_fix: {resp.status_code} {resp.text[:300]}")

if resp.status_code in [200, 201]:
    ds_id = resp.json().get("id")
    print(f"  Created with ID: {ds_id}")

# List all datasets
print("\n--- All datasets ---")
resp = s.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers={"Authorization": f"Bearer {token}"})
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", "") or "dim_mahasiswa" in ds.get("table_name", "") or "fact_khs" in ds.get("table_name", ""):
            print(f"  ID={ds['id']} | {ds['table_name']} | schema={ds.get('schema','?')}")
