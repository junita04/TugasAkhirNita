"""
Create virtual dataset for IPK distribution with SQL CASE bins,
then update chart 100 to use bar chart
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

# Step 1: Create virtual dataset with IPK bins
print("=" * 70)
print("STEP 1: Create virtual dataset for IPK distribution")
print("=" * 70)

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

# Try creating virtual dataset via API
r = s.post(f"{BASE}/api/v1/dataset/", json={
    "database": 2,  # Academic Trino database
    "schema": "gold",
    "table_name": "ipk_distribution_aktif",
    "sql": virtual_sql,
    "description": "Distribusi IPK mahasiswa aktif berdasarkan rentang",
})
print(f"Create dataset: {r.status_code}")
if r.status_code in [200, 201]:
    ds_id = r.json()["id"]
    print(f"Dataset created: id={ds_id}")
else:
    print(f"Error: {r.text[:300]}")
    # Try alternative: check if dataset already exists
    r2 = s.get(f"{BASE}/api/v1/dataset/?q=(page:0,page_size:100)")
    if r2.status_code == 200:
        datasets = r2.json().get("result", [])
        for ds in datasets:
            if "ipk_distribution" in ds.get("table_name", "").lower():
                ds_id = ds["id"]
                print(f"Found existing dataset: id={ds_id}")
                break
        else:
            print("No existing IPK distribution dataset found")
            ds_id = None

if 'ds_id' not in dir():
    ds_id = None
    print("Could not create or find dataset")

# Step 2: Test the virtual dataset
if ds_id:
    print(f"\n{'='*70}")
    print(f"STEP 2: Test virtual dataset {ds_id}")
    print(f"{'='*70}")
    
    # Test query
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
    r = s.post(f"{BASE}/api/v1/chart/data", json=test_qc)
    print(f"Test query: {r.status_code}")
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

# Step 3: Update chart 100 to use bar chart with virtual dataset
if ds_id:
    print(f"\n{'='*70}")
    print(f"STEP 3: Update chart 100")
    print(f"{'='*70}")
    
    bar_params = {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "rentang_ipk",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
        "groupby": [],
        "row_limit": 10,
        "show_legend": False,
        "rich_tooltip": True,
        "stack": False,
        "color_scheme": "supersetCategory10",
        "truncate_metric": True,
        "show_bar_value": True,
    }
    
    bar_qc = {
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [{
            "time_range": "No filter",
            "granularity_sqla": None,
            "row_limit": 10,
            "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
            "columns": ["rentang_ipk"],
        }],
        "form_data": bar_params,
        "result_format": "json",
        "result_type": "full",
    }
    
    # Test
    r = s.post(f"{BASE}/api/v1/chart/data", json=bar_qc)
    print(f"Bar chart test: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if "result" in data and data["result"]:
            d = data["result"][0].get("data", [])
            print(f"Data: {d}")
            
            # Update chart 100
            r_put = s.put(f"{BASE}/api/v1/chart/100", json={
                "params": json.dumps(bar_params),
                "viz_type": "echarts_timeseries_bar",
                "datasource_id": ds_id,
                "datasource_type": "table",
                "query_context": json.dumps(bar_qc),
            })
            print(f"Update chart 100: {r_put.status_code}")
    else:
        try:
            print(f"Error: {r.json()}")
        except:
            print(f"Error: {r.text[:300]}")
