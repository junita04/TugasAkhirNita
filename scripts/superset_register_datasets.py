import requests
import json

SUPERSET_URL = "http://superset:8088"

# Login
r = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("=" * 80)
print("STEP 1: Check Trino for _fix tables")
print("=" * 80)

# Try to query Trino via Superset's SQL interface to check if _fix tables exist
# First, let's try to register the new datasets via the API

# Check if we can list tables in gold schema
resp = requests.get(f"{SUPERSET_URL}/api/v1/database/1/tables/", headers=headers)
if resp.status_code == 200:
    tables = resp.json().get("result", [])
    print(f"Total tables in database: {len(tables)}")
    # Filter for gold schema tables
    gold_tables = [t for t in tables if t.get("schema") == "gold"]
    print(f"Gold schema tables: {len(gold_tables)}")
    for t in gold_tables:
        print(f"  {t.get('table')} | columns={t.get('columns', '?')}")
else:
    print(f"Error listing tables: {resp.status_code} {resp.text[:200]}")

# Check for _fix tables specifically
print("\n--- Checking for _fix tables ---")
fix_tables = [t for t in tables if "_fix" in str(t.get("table", ""))]
print(f"Found _fix tables: {len(fix_tables)}")
for t in fix_tables:
    print(f"  {t.get('schema')}.{t.get('table')}")

print("\n" + "=" * 80)
print("STEP 2: Register new datasets via Superset API")
print("=" * 80)

# Register dim_mahasiswa_fix
new_datasets = [
    {"schema": "gold", "table_name": "dim_mahasiswa_fix"},
    {"schema": "gold", "table_name": "fact_khs_fix"},
]

for ds_info in new_datasets:
    # Check if dataset already exists
    resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(filters:!((col:table_name,opr:eq,value:'{ds_info['table_name']}')))", headers=headers)
    existing = resp.json().get("result", [])
    if existing:
        print(f"  Dataset already exists: {ds_info['table_name']} (ID={existing[0]['id']})")
        continue
    
    # Create new dataset
    payload = {
        "database": 1,  # Academic Trino
        "schema": ds_info["schema"],
        "table_name": ds_info["table_name"],
    }
    resp = requests.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        ds_id = resp.json().get("id")
        print(f"  Created dataset: {ds_info['table_name']} (ID={ds_id})")
    else:
        print(f"  Error creating {ds_info['table_name']}: {resp.status_code} {resp.text[:200]}")

print("\n" + "=" * 80)
print("STEP 3: Refresh datasets to get columns")
print("=" * 80)

# Refresh the new datasets to get column metadata
resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            ds_id = ds["id"]
            # Refresh columns
            resp2 = requests.put(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}/refresh", headers=headers)
            print(f"  Refreshed {ds['table_name']}: {resp2.status_code}")

print("\n" + "=" * 80)
print("STEP 4: Verify datasets and columns")
print("=" * 80)

resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            ds_id = ds["id"]
            # Get dataset details with columns
            resp2 = requests.get(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}", headers=headers)
            if resp2.status_code == 200:
                detail = resp2.json().get("result", {})
                cols = detail.get("columns", [])
                print(f"\n  {ds['table_name']} (ID={ds_id}):")
                print(f"    Columns: {len(cols)}")
                for c in cols[:5]:
                    print(f"      {c.get('column_name')} | type={c.get('type')}")
                if len(cols) > 5:
                    print(f"      ... and {len(cols)-5} more")
            else:
                print(f"  Error getting details for {ds['table_name']}: {resp2.status_code}")

print("\nDONE.")
