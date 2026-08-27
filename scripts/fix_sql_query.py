"""
Fix the SQL query - use column alias in ORDER BY
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

# Fixed SQL - use column alias in ORDER BY
proper_sql = """
SELECT
    CASE
        WHEN ipk < 2.00 THEN '1. < 2.00'
        WHEN ipk >= 2.00 AND ipk < 2.50 THEN '2. 2.00-2.49'
        WHEN ipk >= 2.50 AND ipk < 3.00 THEN '3. 2.50-2.99'
        WHEN ipk >= 3.00 AND ipk < 3.50 THEN '4. 3.00-3.49'
        WHEN ipk >= 3.50 AND ipk <= 4.00 THEN '5. 3.50-4.00'
        ELSE '6. Tidak Valid'
    END AS rentang_ipk,
    COUNT(*) AS jumlah_mahasiswa
FROM iceberg.gold.data_referensi_mahasiswa
WHERE status_mahasiswa = 'AKTIF'
  AND ipk IS NOT NULL
  AND ipk BETWEEN 0 AND 4
GROUP BY 1
ORDER BY rentang_ipk
"""

print("Updating dataset 18 SQL...")
r = s.put(f"{BASE}/api/v1/dataset/18", json={"sql": proper_sql})
print(f"Update dataset: {r.status_code}")

# Test the dataset
print("\nTesting dataset 18...")
test_qc = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": ["count"],
        "columns": ["rentang_ipk", "jumlah_mahasiswa"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=test_qc)
print(f"Test: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"Data: {d}")
else:
    try:
        print(f"Error: {r.json()}")
    except:
        print(f"Error: {r.text[:300]}")

# Try simpler query
print("\nSimpler query...")
test_qc2 = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["rentang_ipk", "jumlah_mahasiswa"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=test_qc2)
print(f"Test2: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"Data: {d}")
