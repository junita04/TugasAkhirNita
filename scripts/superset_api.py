import requests
import json

BASE = "http://superset:8088"

# 1. Get access token via login
s = requests.Session()

# Login
resp = s.post(f"{BASE}/api/v1/security/login", json={
    "username": "admin",
    "password": "change-me",
    "provider": "db"
})
print("Login status:", resp.status_code)
token = resp.json().get("access_token", "")
print("Token:", token[:30] + "..." if token else "NONE")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 2. Get CSRF token
csrf = s.get(f"{BASE}/api/v1/security/csrf_token/", headers=headers)
print("CSRF status:", csrf.status_code)
csrf_token = csrf.json().get("result", "")
headers["X-CSRFToken"] = csrf_token

# 3. List existing databases
dbs = s.get(f"{BASE}/api/v1/database/", headers=headers)
print("\nDatabases:", dbs.status_code)
for db in dbs.json().get("result", []):
    print(f"  id={db['id']} name={db['database_name']} backend={db.get('backend')}")

# 4. List existing datasets
datasets = s.get(f"{BASE}/api/v1/dataset/", headers=headers)
print("\nDatasets:", datasets.status_code)
for ds in datasets.json().get("result", []):
    print(f"  id={ds['id']} table={ds.get('table_name')} db_id={ds.get('database', {}).get('id')}")
