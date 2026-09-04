"""
CHECK SUPERSET STATE - Audit existing configuration
"""
import requests
import json

SUPERSET_URL = "http://superset:8088"
LOGIN_URL = f"{SUPERSET_URL}/api/v1/security/login"

# Login
login_data = {
    "username": "admin",
    "password": "admin",
    "provider": "db",
    "refresh": True
}

session = requests.Session()
resp = session.post(LOGIN_URL, json=login_data)
if resp.status_code != 200:
    print(f"Login failed: {resp.status_code} {resp.text}")
    exit(1)

token = resp.json()["access_token"]
session.headers.update({
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
})

print("=" * 80)
print("SUPERSET STATE AUDIT")
print("=" * 80)

# 1. Database connections
print("\n--- DATABASE CONNECTIONS ---")
resp = session.get(f"{SUPERSET_URL}/api/v1/database/")
if resp.status_code == 200:
    dbs = resp.json().get("result", [])
    for db in dbs:
        print(f"  ID={db['id']} | {db['database_name']} | backend={db.get('backend','?')}")
else:
    print(f"  Error: {resp.status_code}")

# 2. Datasets
print("\n--- DATASETS ---")
resp = session.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:100)")
if resp.status_code == 200:
    datasets = resp.json().get("result", [])
    for ds in datasets:
        print(f"  ID={ds['id']} | {ds['table_name']} | db={ds.get('database',{}).get('database_name','?')} | schema={ds.get('schema','?')}")
else:
    print(f"  Error: {resp.status_code}")

# 3. Charts
print("\n--- CHARTS ---")
resp = session.get(f"{SUPERSET_URL}/api/v1/chart/?q=(page_size:100)")
if resp.status_code == 200:
    charts = resp.json().get("result", [])
    for ch in charts:
        print(f"  ID={ch['id']} | {ch['slice_name']} | type={ch.get('viz_type','?')}")
else:
    print(f"  Error: {resp.status_code}")

# 4. Dashboards
print("\n--- DASHBOARDS ---")
resp = session.get(f"{SUPERSET_URL}/api/v1/dashboard/?q=(page_size:100)")
if resp.status_code == 200:
    dashboards = resp.json().get("result", [])
    for d in dashboards:
        print(f"  ID={d['id']} | {d['dashboard_title']} | slug={d.get('slug','?')}")
else:
    print(f"  Error: {resp.status_code}")

# 5. Available viz types
print("\n--- AVAILABLE VIZ TYPES ---")
resp = session.get(f"{SUPERSET_URL}/api/v1/chart/related/viz_type")
if resp.status_code == 200:
    viz_types = resp.json().get("result", [])
    for vt in viz_types[:20]:
        print(f"  {vt['text']} ({vt['value']})")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
