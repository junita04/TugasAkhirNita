import requests
import json

SUPERSET_URL = "http://superset:8088"

# Get JWT token
r = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json()["access_token"]

# Get CSRF token using JWT
headers_jwt = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
r_csrf = requests.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/", headers=headers_jwt)
print(f"CSRF via JWT: {r_csrf.status_code} {r_csrf.text[:200]}")

if r_csrf.status_code == 200:
    csrf_token = r_csrf.json().get("result", "")
    print(f"CSRF token: {csrf_token[:50]}...")
    
    # Now try to create dataset with CSRF
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
        "Referer": f"{SUPERSET_URL}/",
    }
    
    payload = {
        "database": 1,
        "schema": "gold",
        "table_name": "dim_mahasiswa_fix",
    }
    resp = requests.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    print(f"Create dim_mahasiswa_fix: {resp.status_code} {resp.text[:300]}")
    
    payload["table_name"] = "fact_khs_fix"
    resp = requests.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    print(f"Create fact_khs_fix: {resp.status_code} {resp.text[:300]}")
else:
    print("CSRF token not available, trying alternative...")
    # Try with session-based auth
    s = requests.Session()
    # Login via form
    s.post(f"{SUPERSET_URL}/login/", data={"username": "admin", "password": "change-me"})
    # Get CSRF from HTML page
    r2 = s.get(f"{SUPERSET_URL}/superset/csrf_token/")
    csrf = r2.text if r2.status_code == 200 else ""
    print(f"HTML CSRF: {csrf[:50]}")
    
    # Try with headers
    headers = {
        "X-CSRFToken": csrf,
        "Content-Type": "application/json",
        "Referer": f"{SUPERSET_URL}/",
    }
    
    payload = {
        "database": 1,
        "schema": "gold",
        "table_name": "dim_mahasiswa_fix",
    }
    resp = s.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    print(f"Create dim_mahasiswa_fix (session): {resp.status_code} {resp.text[:300]}")

# List all _fix datasets
print("\n--- All _fix datasets ---")
resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers_jwt)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            print(f"  ID={ds['id']} | {ds['table_name']} | schema={ds.get('schema','?')}")
else:
    print(f"Error: {resp.status_code}")
