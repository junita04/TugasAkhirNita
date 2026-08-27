"""
Create virtual dataset with correct database ID
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

# Create with database=1
r = s.post(f"{BASE}/api/v1/dataset/", json={
    "database": 1,
    "table_name": "ipk_distribution_aktif",
    "sql": virtual_sql,
})
print(f"Create dataset: {r.status_code}")
if r.status_code in [200, 201]:
    ds_id = r.json()["id"]
    print(f"Dataset created: id={ds_id}")
    
    # Test it
    test_qc = {
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [{
            "time_range": "No filter",
            "granularity_sqla": None,
            "row_limit": 10,
            "metrics": ["jumlah_mahasiswa"],
            "columns": ["rentang_ipk"],
        }],
        "form_data": {},
        "result_format": "json",
        "result_type": "full",
    }
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=test_qc)
    print(f"Test query: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            d = data["result"][0].get("data", [])
            print(f"Data: {d}")
else:
    print(f"Error: {r.text[:500]}")
