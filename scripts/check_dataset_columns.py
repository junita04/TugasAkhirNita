"""
Check existing Superset dataset columns and refresh if needed.
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

def api_put(token, path, data):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.put(f"{SUPERSET}{path}", headers=headers, json=data)
    return r

token = get_jwt_token()

# Check dim_mahasiswa dataset (ID=27)
print("=== Dataset dim_mahasiswa (ID=27) ===")
ds = api_get(token, "/api/v1/dataset/27")
print(f"Table: {ds.get('result', {}).get('table_name')}")
print(f"Schema: {ds.get('result', {}).get('schema')}")
print(f"Database: {ds.get('result', {}).get('database', {}).get('database_name')}")

columns = ds.get("result", {}).get("columns", [])
print(f"Columns ({len(columns)}):")
for col in columns:
    print(f"  {col.get('column_name')} ({col.get('type')})")

# Check if columns need refresh
print("\n=== Refreshing dataset columns ===")
r = api_put(token, "/api/v1/dataset/27/refresh", {})
print(f"Refresh status: {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.text[:200]}")

# Check fact_khs dataset (ID=28)
print("\n=== Dataset fact_khs (ID=28) ===")
ds2 = api_get(token, "/api/v1/dataset/28")
print(f"Table: {ds2.get('result', {}).get('table_name')}")
columns2 = ds2.get("result", {}).get("columns", [])
print(f"Columns ({len(columns2)}):")
for col in columns2:
    print(f"  {col.get('column_name')} ({col.get('type')})")

# Check training_dataset (ID=29)
print("\n=== Dataset training_dataset (ID=29) ===")
ds3 = api_get(token, "/api/v1/dataset/29")
print(f"Table: {ds3.get('result', {}).get('table_name')}")
columns3 = ds3.get("result", {}).get("columns", [])
print(f"Columns ({len(columns3)}):")
for col in columns3:
    print(f"  {col.get('column_name')} ({col.get('type')})")

# Check inference_dataset (ID=30)
print("\n=== Dataset inference_dataset (ID=30) ===")
ds4 = api_get(token, "/api/v1/dataset/30")
print(f"Table: {ds4.get('result', {}).get('table_name')}")
columns4 = ds4.get("result", {}).get("columns", [])
print(f"Columns ({len(columns4)}):")
for col in columns4:
    print(f"  {col.get('column_name')} ({col.get('type')})")
