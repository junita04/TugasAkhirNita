"""
Check if virtual dataset exists, then try to use it for chart 100
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

# List all datasets
print("All datasets:")
r = s.get(f"{BASE}/api/v1/dataset/?q=(page:0,page_size:100)")
if r.status_code == 200:
    for ds in r.json().get("result", []):
        print(f"  id={ds['id']}, table={ds['table_name']}, db={ds.get('database',{}).get('database_name','?')}")

# Try creating via SQL Lab approach
print("\nTrying direct SQL execution...")

# Execute the SQL to create a temporary table
sql = """
CREATE OR REPLACE VIEW iceberg.gold.v_ipk_distribution_aktif AS
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
"""

# Try executing via Superset SQL execution API
r = s.post(f"{BASE}/api/v1/sqllab/execute/", json={
    "database_id": 1,
    "sql": sql,
    "schema": "gold",
})
print(f"Execute SQL: {r.status_code}")
if r.status_code == 200:
    print(f"Result: {r.json()}")
else:
    print(f"Error: {r.text[:300]}")
