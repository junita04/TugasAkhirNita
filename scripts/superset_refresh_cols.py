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

# All headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "X-CSRFToken": csrf_token,
    "Referer": f"{SUPERSET_URL}/",
}

print("=" * 80)
print("STEP 1: Refresh columns for _fix datasets")
print("=" * 80)

for ds_id in [34, 35]:
    resp = requests.put(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}/refresh", headers=headers)
    print(f"  Refresh dataset {ds_id}: {resp.status_code} {resp.text[:200]}")

# Get column info
for ds_id in [34, 35]:
    resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}", headers=jwt_headers)
    if resp.status_code == 200:
        detail = resp.json().get("result", {})
        cols = detail.get("columns", [])
        col_names = [c.get("column_name") for c in cols]
        print(f"  Dataset {ds_id} ({detail.get('table_name')}): {len(cols)} columns")
        print(f"    {', '.join(col_names[:10])}")

print("\n" + "=" * 80)
print("STEP 2: List all datasets for reference")
print("=" * 80)

resp = requests.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=jwt_headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            print(f"  ID={ds['id']} | {ds['table_name']} | schema={ds.get('schema','?')}")

print("\nDONE.")
