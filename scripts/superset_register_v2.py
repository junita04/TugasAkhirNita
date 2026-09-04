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
print("REGISTER _fix DATASETS IN SUPERSET")
print("=" * 80)

# Register dim_mahasiswa_fix and fact_khs_fix
new_datasets = [
    {"schema": "gold", "table_name": "dim_mahasiswa_fix"},
    {"schema": "gold", "table_name": "fact_khs_fix"},
]

created_ids = {}
for ds_info in new_datasets:
    payload = {
        "database": 1,  # Academic Trino
        "schema": ds_info["schema"],
        "table_name": ds_info["table_name"],
    }
    resp = requests.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        ds_id = resp.json().get("id")
        created_ids[ds_info["table_name"]] = ds_id
        print(f"OK: {ds_info['table_name']} -> ID={ds_id}")
    else:
        print(f"ERROR: {resp.status_code} {resp.text[:200]}")

print("\n" + "=" * 80)
print("REFRESH COLUMNS")
print("=" * 80)

# Refresh all _fix datasets
resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            ds_id = ds["id"]
            resp2 = requests.put(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}/refresh", headers=headers)
            print(f"  Refresh {ds['table_name']}: {resp2.status_code}")
            # Get column info
            resp3 = requests.get(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}", headers=headers)
            if resp3.status_code == 200:
                detail = resp3.json().get("result", {})
                cols = detail.get("columns", [])
                col_names = [c.get("column_name") for c in cols]
                print(f"    Columns ({len(cols)}): {', '.join(col_names[:10])}")

print("\n" + "=" * 80)
print("VERIFY ALL _fix DATASETS")
print("=" * 80)

resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            print(f"  ID={ds['id']} | {ds['table_name']} | schema={ds.get('schema','?')}")

print("\nDONE.")
