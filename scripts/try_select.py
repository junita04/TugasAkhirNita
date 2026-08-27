"""
Try creating virtual dataset via SQL execution (SELECT, not DDL)
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

# Try SELECT query (not DDL)
sql = """
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

r = s.post(f"{BASE}/api/v1/sqllab/execute/", json={
    "database_id": 1,
    "sql": sql,
    "schema": "gold",
})
print(f"Execute SQL: {r.status_code}")
if r.status_code == 200:
    result = r.json()
    print(f"Status: {result.get('status')}")
    data = result.get("data", [])
    print(f"Rows: {len(data)}")
    for row in data:
        print(f"  {row}")
else:
    print(f"Error: {r.text[:500]}")

# Also try the dataset creation with a simpler approach
print("\nTrying dataset creation with schema...")
r = s.post(f"{BASE}/api/v1/dataset/", json={
    "database": 1,
    "schema": "gold",
    "table_name": "ipk_dist_view",
    "sql": "SELECT 1 AS rentang_ipk, 100 AS jumlah_mahasiswa",
})
print(f"Simple dataset: {r.status_code}")
if r.status_code in [200, 201]:
    print(f"Created: {r.json()}")
else:
    print(f"Error: {r.text[:300]}")
