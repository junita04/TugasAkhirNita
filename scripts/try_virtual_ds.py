"""
Try different approaches to create virtual dataset
"""
import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

s = api()

# First, check what databases are available
print("Databases:")
r = s.get(f"{BASE}/api/v1/database/")
if r.status_code == 200:
    for db in r.json().get("result", []):
        print(f"  id={db['id']}, name={db['database_name']}")

# Check what schemas are available in database 2
print("\nSchemas in database 2:")
r = s.get(f"{BASE}/api/v1/database/2/schemas/")
if r.status_code == 200:
    schemas = r.json().get("result", [])
    for sch in schemas[:20]:
        print(f"  {sch}")

# Try creating dataset with minimal fields
print("\nTrying to create virtual dataset...")
virtual_sql = """
SELECT
    CASE
        WHEN ipk < 2.00 THEN '1. < 2.00'
        WHEN ipk >= 2.00 AND ipk < 2.50 THEN '2. 2.00 - 2.49'
        WHEN ipk >= 2.50 AND ipk < 3.00 THEN '3. 2.50 - 2.99'
        WHEN ipk >= 3.00 AND ipk < 3.50 THEN '4. 3.00 - 3.49'
        WHEN ipk >= 3.50 AND ipk <= 4.00 THEN '5. 3.50 - 4.00'
        ELSE '6. Tidak Valid'
    END AS rentang_ipk,
    COUNT(*) AS jumlah_mahasiswa
FROM iceberg.gold.data_referensi_mahasiswa
WHERE UPPER(TRIM(status_mahasiswa)) = 'AKTIF'
  AND ipk IS NOT NULL
  AND ipk BETWEEN 0 AND 4
GROUP BY 1
ORDER BY
    CASE
        WHEN ipk < 2.00 THEN 1
        WHEN ipk >= 2.00 AND ipk < 2.50 THEN 2
        WHEN ipk >= 2.50 AND ipk < 3.00 THEN 3
        WHEN ipk >= 3.00 AND ipk < 3.50 THEN 4
        WHEN ipk >= 3.50 AND ipk <= 4.00 THEN 5
        ELSE 6
    END
"""

# Approach 1: Try with just required fields
r = s.post(f"{BASE}/api/v1/dataset/", json={
    "database": 2,
    "table_name": "ipk_distribution_aktif",
    "sql": virtual_sql,
})
print(f"Approach 1: {r.status_code}")
if r.status_code in [200, 201]:
    ds_id = r.json()["id"]
    print(f"Dataset created: id={ds_id}")
else:
    print(f"Error: {r.text[:300]}")

# Approach 2: Try with schema
if r.status_code not in [200, 201]:
    r = s.post(f"{BASE}/api/v1/dataset/", json={
        "database": 2,
        "schema": "default",
        "table_name": "ipk_distribution_aktif",
        "sql": virtual_sql,
    })
    print(f"Approach 2: {r.status_code}")
    if r.status_code in [200, 201]:
        ds_id = r.json()["id"]
        print(f"Dataset created: id={ds_id}")
    else:
        print(f"Error: {r.text[:300]}")

# Approach 3: Try with database卵巢
if r.status_code not in [200, 201]:
    r = s.post(f"{BASE}/api/v1/dataset/", json={
        "database": {"id": 2},
        "table_name": "ipk_distribution_aktif",
        "sql": virtual_sql,
    })
    print(f"Approach 3: {r.status_code}")
    if r.status_code in [200, 201]:
        ds_id = r.json()["id"]
        print(f"Dataset created: id={ds_id}")
    else:
        print(f"Error: {r.text[:300]}")
