import requests
import json

SUPERSET_URL = "http://superset:8088"

# Login with correct password
r = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json={
    "username": "admin",
    "password": "change-me",
    "provider": "db",
    "refresh": True
})
print(f"Login: {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.text[:200]}")
    exit(1)

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 1. Database connections
print("\n--- DATABASES ---")
resp = requests.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers)
if resp.status_code == 200:
    for db in resp.json().get("result", []):
        print(f"  ID={db['id']} | {db['database_name']} | backend={db.get('backend','?')}")
else:
    print(f"  Error: {resp.status_code} {resp.text[:200]}")

# 2. Datasets
print("\n--- DATASETS ---")
resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        db_name = ds.get("database", {}).get("database_name", "?") if ds.get("database") else "?"
        print(f"  ID={ds['id']} | {ds['table_name']} | db={db_name} | schema={ds.get('schema','?')}")
else:
    print(f"  Error: {resp.status_code} {resp.text[:200]}")

# 3. Charts
print("\n--- CHARTS ---")
resp = requests.get(f"{SUPERSET_URL}/api/v1/chart/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    charts = resp.json().get("result", [])
    print(f"  Total charts: {len(charts)}")
    for ch in charts[:30]:
        print(f"  ID={ch['id']} | {ch['slice_name']} | type={ch.get('viz_type','?')}")
else:
    print(f"  Error: {resp.status_code} {resp.text[:200]}")

# 4. Dashboards
print("\n--- DASHBOARDS ---")
resp = requests.get(f"{SUPERSET_URL}/api/v1/dashboard/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for d in resp.json().get("result", []):
        print(f"  ID={d['id']} | {d['dashboard_title']} | slug={d.get('slug','?')}")
else:
    print(f"  Error: {resp.status_code} {resp.text[:200]}")

# Save token for later use
with open("/tmp/superset_token.json", "w") as f:
    json.dump({"token": token}, f)
print("\nToken saved to /tmp/superset_token.json")
