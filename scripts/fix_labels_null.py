"""
FINAL REVISION: Fix <NULL> labels, chart titles, and clean up all text.
No data changes - only presentation layer.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
import json, requests

app = create_app()
app.app_context().push()

from superset.models.slice import Slice
from superset.models.dashboard import Dashboard

SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("STEP 1: Fix <NULL> in status_kelulusan chart (ID=156)")
print("=" * 60)

# Chart 156: Distribusi Status Kelulusan - has <NULL> because
# dim_mahasiswa.status_kelulusan has empty strings for active students
# Fix: use CASE WHEN to rename empty/NULL to "Belum Lulus"
s156 = db.session.query(Slice).get(156)
if s156:
    s156.viz_type = "pie"
    s156.params = json.dumps({
        "viz_type": "pie",
        "groupby": [],
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": "CASE WHEN status_kelulusan IS NULL OR status_kelulusan = '' THEN 'Belum Lulus' ELSE status_kelulusan END",
            "label": "status_kelulusan_clean"
        }],
        "row_limit": 100,
    })
    s156.query_context = json.dumps({
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "columns": [{
                "expressionType": "SQL",
                "sqlExpression": "CASE WHEN status_kelulusan IS NULL OR status_kelulusan = '' THEN 'Belum Lulus' ELSE status_kelulusan END",
                "label": "status_kelulusan_clean"
            }],
            "row_limit": 100,
        }],
        "result_format": "json", "result_type": "full",
    })
    print("  Fixed chart 156: <NULL> -> 'Belum Lulus'")

print("\n" + "=" * 60)
print("STEP 2: Rename all chart titles")
print("=" * 60)

renames = {
    # Academic KPIs
    145: "Total Mahasiswa",
    146: "Mahasiswa Aktif",
    147: "Mahasiswa Lulus",
    148: "Mahasiswa Tepat Waktu",
    149: "Mahasiswa Terlambat",
    150: "Rata-rata IPK",
    151: "Rata-rata IP",
    152: "Rata-rata Total SKS",
    # Academic Charts
    153: "Distribusi Mahasiswa Berdasarkan Angkatan",
    154: "Distribusi Jenis Kelamin",
    155: "Distribusi Status Mahasiswa",
    156: "Distribusi Status Kelulusan",
    157: "Status Kelulusan Berdasarkan Angkatan",
    158: "Status Mahasiswa Berdasarkan Angkatan",
    159: "Rata-rata IPK Berdasarkan Angkatan",
    160: "Rata-rata IP Berdasarkan Angkatan",
    161: "Rata-rata Total SKS Berdasarkan Angkatan",
    162: "Rata-rata Selisih SKS Berdasarkan Angkatan",
    # Prediction KPIs
    163: "Mahasiswa yang Diprediksi",
    164: "Prediksi Tepat Waktu",
    165: "Prediksi Terlambat",
    166: "Persentase Prediksi Tepat Waktu",
    167: "Persentase Prediksi Terlambat",
    # Prediction Charts
    168: "Distribusi Prediksi Kelulusan",
    169: "Prediksi Kelulusan Berdasarkan Angkatan",
    170: "Persentase Prediksi Berdasarkan Angkatan",
    171: "Detail Prediksi Mahasiswa",
    172: "Distribusi Label Data Training",
}

for cid, name in renames.items():
    s = db.session.query(Slice).get(cid)
    if s and s.slice_name != name:
        old = s.slice_name
        s.slice_name = name
        print(f"  {cid}: '{old}' -> '{name}'")
db.session.commit()

print("\n" + "=" * 60)
print("STEP 3: Fix KPI chart titles in layout")
print("=" * 60)

# Update layout metadata with correct slice names
dash = db.session.query(Dashboard).get(6)
if dash and dash.position_json:
    pos = json.loads(dash.position_json)
    for k, v in pos.items():
        if k.startswith("CHART-"):
            cid = v.get("meta", {}).get("chartId")
            if cid in renames:
                v["meta"]["sliceName"] = renames[cid]
    dash.position_json = json.dumps(pos)
    print("  Layout metadata updated")

print("\n" + "=" * 60)
print("STEP 4: Validate all charts")
print("=" * 60)

all_ids = list(range(145, 173))
pass_count = 0
fail_count = 0
for cid in all_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            print(f"  PASS  ID={cid:3d}  {s.viz_type:30s}  {s.slice_name}")
            pass_count += 1
        else:
            print(f"  FAIL  ID={cid:3d}  {s.slice_name}  empty")
            fail_count += 1
    else:
        err = r.text[:80] if r.text else ""
        print(f"  FAIL  ID={cid:3d}  {s.slice_name}  HTTP {r.status_code} {err}")
        fail_count += 1

print(f"\nRESULT: {pass_count} PASS, {fail_count} FAIL")
print(f"URL: http://localhost:8088/superset/dashboard/6/")
