"""
Check Superset state and create/update datasets.
Uses JWT authentication with CSRF token.
"""
import requests
import json
import time

SUPERSET = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "change-me"

def get_jwt_token():
    """Get JWT access token."""
    r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db",
        "refresh": True
    })
    return r.json().get("access_token")

def get_csrf_token(token):
    """Get CSRF token."""
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}/api/v1/security/csrf_token/", headers=headers)
    return r.json().get("result")

def api_get(token, path):
    """GET request."""
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}{path}", headers=headers)
    return r.json()

def api_post(token, path, data, csrf_token=None):
    """POST request."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
    r = requests.post(f"{SUPERSET}{path}", headers=headers, json=data)
    return r

print("=" * 70)
print("SUPERSET STATE CHECK")
print("=" * 70)

# Get token
token = get_jwt_token()
if not token:
    print("ERROR: Cannot get JWT token")
    exit(1)
print(f"JWT token: OK")

csrf = get_csrf_token(token)
print(f"CSRF token: {'OK' if csrf else 'NONE'}")

# Check databases
dbs = api_get(token, "/api/v1/database/")
print(f"\nDatabases: {dbs.get('count', 0)}")
for db in dbs.get("result", []):
    print(f"  ID={db['id']} Name={db['database_name']}")

# Check datasets
datasets = api_get(token, "/api/v1/dataset/")
print(f"\nDatasets: {datasets.get('count', 0)}")
for ds in datasets.get("result", []):
    print(f"  ID={ds['id']} Table={ds.get('table_name', 'N/A')} DB={ds.get('database', {}).get('database_name', 'N/A')}")

# Check dashboards
dashboards = api_get(token, "/api/v1/dashboard/")
print(f"\nDashboards: {dashboards.get('count', 0)}")
for d in dashboards.get("result", []):
    print(f"  ID={d['id']} Title={d.get('dashboard_title', 'N/A')}")

# Check charts
charts = api_get(token, "/api/v1/chart/")
print(f"\nCharts: {charts.get('count', 0)}")

# Verify Trino data
print("\n" + "=" * 70)
print("TRINO DATA VERIFICATION")
print("=" * 70)

# Use Superset to query Trino
db_id = dbs["result"][0]["id"] if dbs.get("result") else None
if db_id:
    # Query via Superset SQL
    sql_data = {
        "database_id": db_id,
        "sql": "SELECT COUNT(*) as cnt FROM iceberg.gold.dim_mahasiswa",
        "schema": "gold"
    }
    r = api_post(token, "/api/v1/sqllab/execute/", sql_data, csrf)
    print(f"SQL Lab test: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"  Result: {result}")
    else:
        print(f"  Error: {r.text[:200]}")
