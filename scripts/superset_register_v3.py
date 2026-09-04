import requests
import json

SUPERSET_URL = "http://superset:8088"

# Create session
s = requests.Session()

# Login via form to get CSRF token
r = s.post(f"{SUPERSET_URL}/login/", data={"username": "admin", "password": "change-me"})
print(f"Form login: {r.status_code}")

# Get CSRF token
r_csrf = s.get(f"{SUPERSET_URL}/superset/csrf_token/")
csrf_token = r_csrf.text if r_csrf.status_code == 200 else ""
print(f"CSRF token: {len(csrf_token)} chars")

# Now get JWT token
r_jwt = s.post(f"{SUPERSET_URL}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
print(f"JWT login: {r_jwt.status_code}")
if r_jwt.status_code == 200:
    token = r_jwt.json()["access_token"]
else:
    print(f"JWT error: {r_jwt.text[:200]}")
    # Try without JWT, use session cookies + CSRF
    token = None

# Set headers
if token:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
else:
    headers = {"X-CSRFToken": csrf_token, "Content-Type": "application/json", "Referer": f"{SUPERSET_URL}/"}

print("\n" + "=" * 80)
print("REGISTER _fix DATASETS")
print("=" * 80)

new_datasets = [
    {"schema": "gold", "table_name": "dim_mahasiswa_fix"},
    {"schema": "gold", "table_name": "fact_khs_fix"},
]

for ds_info in new_datasets:
    payload = {
        "database": 1,
        "schema": ds_info["schema"],
        "table_name": ds_info["table_name"],
    }
    resp = s.post(f"{SUPERSET_URL}/api/v1/dataset/", headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        ds_id = resp.json().get("id")
        print(f"OK: {ds_info['table_name']} -> ID={ds_id}")
    else:
        print(f"ERROR: {resp.status_code} {resp.text[:300]}")

print("\n" + "=" * 80)
print("LIST ALL _fix DATASETS")
print("=" * 80)

resp = s.get(f"{SUPERSET_URL}/api/v1/dataset/?q=(page_size:200)", headers=headers)
if resp.status_code == 200:
    for ds in resp.json().get("result", []):
        if "_fix" in ds.get("table_name", ""):
            ds_id = ds["id"]
            # Refresh columns
            s.put(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}/refresh", headers=headers)
            # Get details
            r2 = s.get(f"{SUPERSET_URL}/api/v1/dataset/{ds_id}", headers=headers)
            if r2.status_code == 200:
                detail = r2.json().get("result", {})
                cols = detail.get("columns", [])
                col_names = [c.get("column_name") for c in cols]
                print(f"  ID={ds_id} | {ds['table_name']} | schema={ds.get('schema','?')} | cols={len(cols)}")
                print(f"    {', '.join(col_names[:8])}")
            else:
                print(f"  ID={ds_id} | {ds['table_name']} | refresh={r2.status_code}")
else:
    print(f"Error: {resp.status_code} {resp.text[:200]}")

print("\nDONE.")
