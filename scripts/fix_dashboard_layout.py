"""
FIX DASHBOARD 6: Proper chart heights + fix echarts_bar + professional layout.
Superset grid: 1 height unit ≈ 8px. 
KPI: 8 units, Charts: 14-16 units, Tables: 14 units.
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
print("STEP 1: Fix echarts_bar charts (159-162)")
print("=" * 60)

# Charts 159-162 use echarts_bar which is NOT registered
# Change them to echarts_timeseries_bar
bar_fixes = {
    159: "Rata-rata IPK per Angkatan",
    160: "Rata-rata IP per Angkatan",
    161: "Rata-rata Total SKS per Angkatan",
    162: "Rata-rata Selisih SKS per Angkatan",
}

for cid, name in bar_fixes.items():
    s = db.session.query(Slice).get(cid)
    if s:
        # Get current params
        params = json.loads(s.params) if s.params else {}
        
        # Change viz_type to echarts_timeseries_bar
        s.viz_type = "echarts_timeseries_bar"
        
        # Ensure proper x_axis for timeseries bar
        # The data needs a groupby column for the x-axis
        # Check what columns are available
        print(f"  Chart {cid}: {name}")
        print(f"    Old viz_type: echarts_bar -> New: echarts_timeseries_bar")
        
        # Ensure metrics is properly set for timeseries
        if "metrics" not in params or not params.get("metrics"):
            params["metrics"] = [{"label": name, "expressionType": "SQL", "sqlExpression": f"AVG({name.split()[-1].lower()})"}]
        
        # Set x_axis to angkatan for proper grouping
        params["x_axis"] = "angkatan"
        params["row_limit"] = 100
        
        s.params = json.dumps(params)
        
        # Update query_context too
        s.query_context = json.dumps({
            "datasource": {"id": 27, "type": "table"},
            "queries": [{
                "columns": ["angkatan"],
                "metrics": [{"label": "value", "expressionType": "SQL", "sqlExpression": f"AVG({name.split()[-1].lower()})"}],
                "row_limit": 100,
                "orderby": [["angkatan", True]]
            }],
            "result_format": "json",
            "result_type": "full",
        })
        db.session.commit()

print("\n" + "=" * 60)
print("STEP 2: Rename chart titles (no V2)")
print("=" * 60)

# Rename all chart titles to remove V2
rename_map = {
    145: "Total Mahasiswa",
    146: "Mahasiswa Aktif",
    147: "Mahasiswa Lulus",
    148: "Tepat Waktu",
    149: "Terlambat",
    150: "Rata-rata IPK",
    151: "Rata-rata IP",
    152: "Rata-rata Total SKS",
    153: "Distribusi Mahasiswa per Angkatan",
    154: "Distribusi Jenis Kelamin",
    155: "Distribusi Status Mahasiswa",
    156: "Distribusi Status Kelulusan",
    157: "Status Kelulusan per Angkatan",
    158: "Status Mahasiswa per Angkatan",
    159: "Rata-rata IPK per Angkatan",
    160: "Rata-rata IP per Angkatan",
    161: "Rata-rata Total SKS per Angkatan",
    162: "Rata-rata Selisih SKS per Angkatan",
    163: "Total Mahasiswa Diprediksi",
    164: "Prediksi Tepat Waktu",
    165: "Prediksi Terlambat",
    166: "Persentase Tepat Waktu",
    167: "Persentase Terlambat",
    168: "Distribusi Prediksi Kelulusan",
    169: "Prediksi Kelulusan per Angkatan",
    170: "Persentase Prediksi per Angkatan",
    171: "Detail Prediksi Mahasiswa",
    172: "Distribusi Label Data Training",
}

for cid, new_name in rename_map.items():
    s = db.session.query(Slice).get(cid)
    if s and s.slice_name != new_name:
        old = s.slice_name
        s.slice_name = new_name
        print(f"  {cid}: '{old}' -> '{new_name}'")
db.session.commit()

print("\n" + "=" * 60)
print("STEP 3: Rebuild Dashboard 6 layout with proper heights")
print("=" * 60)

# Superset grid: width=24 columns, height in units (1 unit ≈ 8px)
# KPI: 8 units high, Charts: 14 units, Tables: 14 units

dash = db.session.query(Dashboard).get(6)

# Chart IDs
A = {
    "total": 145, "aktif": 146, "lulus": 147, "tw": 148, "tl": 149,
    "ipk": 150, "ip": 151, "sks": 152, "angkatan": 153, "jk": 154,
    "status": 155, "kelulusan": 156, "ang_kel": 157, "ang_stat": 158,
    "ipk_ang": 159, "ip_ang": 160, "sks_ang": 161, "selisih_ang": 162,
}
P = {
    "total": 163, "tw": 164, "tl": 165, "ptw": 166, "ptl": 167,
    "dist": 168, "per_ang": 169, "pct_ang": 170, "detail": 171, "label": 172,
}

pos = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {
        "type": "GRID", "id": "GRID_ID",
        "children": [
            "ROW-kpi-akademik",
            "ROW-statistik",
            "ROW-profil-1",
            "ROW-profil-2",
            "ROW-performa-1",
            "ROW-performa-2",
            "ROW-kelulusan",
            "ROW-divider",
            "ROW-kpi-prediksi",
            "ROW-dist-prediksi",
            "ROW-probabilitas",
            "ROW-detail",
        ],
        "parents": []
    },
    "HEADER_ID": {
        "type": "HEADER", "id": "HEADER_ID",
        "meta": {"text": "Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa"}
    },
}

# Helper: create chart container
def make_chart(chart_id, name, width, height, row_id):
    cid = f"CH-{chart_id}"
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {"width": width, "height": height, "chartId": chart_id, "sliceName": name}
    }
    return cid

# Helper: create row
def make_row(row_id, chart_ids):
    pos[row_id] = {
        "type": "ROW", "id": row_id,
        "children": chart_ids,
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"}
    }

# =====================================================
# ROW 1: KPI AKADEMIK (5 KPI, compact)
# =====================================================
make_chart(A["total"], "Total Mahasiswa", 5, 8, "ROW-kpi-akademik")
make_chart(A["aktif"], "Mahasiswa Aktif", 5, 8, "ROW-kpi-akademik")
make_chart(A["lulus"], "Mahasiswa Lulus", 5, 8, "ROW-kpi-akademik")
make_chart(A["tw"], "Tepat Waktu", 5, 8, "ROW-kpi-akademik")
make_chart(A["tl"], "Terlambat", 4, 8, "ROW-kpi-akademik")
make_row("ROW-kpi-akademik", ["CH-145", "CH-146", "CH-147", "CH-148", "CH-149"])

# =====================================================
# ROW 2: STATISTIK AKADEMIK (4 KPI)
# =====================================================
make_chart(A["ipk"], "Rata-rata IPK", 6, 8, "ROW-statistik")
make_chart(A["ip"], "Rata-rata IP", 6, 8, "ROW-statistik")
make_chart(A["sks"], "Rata-rata Total SKS", 6, 8, "ROW-statistik")
make_chart(A["selisih_ang"], "Rata-rata Selisih SKS per Angkatan", 6, 8, "ROW-statistik")
make_row("ROW-statistik", ["CH-150", "CH-151", "CH-152", "CH-162"])

# =====================================================
# ROW 3: PROFIL MAHASISWA (3 charts)
# =====================================================
make_chart(A["angkatan"], "Distribusi Mahasiswa per Angkatan", 8, 14, "ROW-profil-1")
make_chart(A["jk"], "Distribusi Jenis Kelamin", 8, 14, "ROW-profil-1")
make_chart(A["status"], "Distribusi Status Mahasiswa", 8, 14, "ROW-profil-1")
make_row("ROW-profil-1", ["CH-153", "CH-154", "CH-155"])

# =====================================================
# ROW 4: STATUS KELULUSAN (2 charts)
# =====================================================
make_chart(A["kelulusan"], "Distribusi Status Kelulusan", 12, 14, "ROW-profil-2")
make_chart(A["ang_kel"], "Status Kelulusan per Angkatan", 12, 14, "ROW-profil-2")
make_row("ROW-profil-2", ["CH-156", "CH-157"])

# =====================================================
# ROW 5: PERFORMA AKADEMIK - IPK & IP per Angkatan
# =====================================================
make_chart(A["ipk_ang"], "Rata-rata IPK per Angkatan", 12, 14, "ROW-performa-1")
make_chart(A["ip_ang"], "Rata-rata IP per Angkatan", 12, 14, "ROW-performa-1")
make_row("ROW-performa-1", ["CH-159", "CH-160"])

# =====================================================
# ROW 6: PERFORMA AKADEMIK - SKS per Angkatan
# =====================================================
make_chart(A["sks_ang"], "Rata-rata Total SKS per Angkatan", 12, 14, "ROW-performa-2")
make_chart(A["ang_stat"], "Status Mahasiswa per Angkatan", 12, 14, "ROW-performa-2")
make_row("ROW-performa-2", ["CH-161", "CH-158"])

# =====================================================
# ROW 7: STATUS KELULUSAN (remaining)
# =====================================================
# Already covered in row 4, skip

# =====================================================
# DIVIDER
# =====================================================
pos["ROW-divider"] = {
    "type": "ROW", "id": "ROW-divider",
    "children": ["CH-div"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CH-div"] = {
    "type": "CHART", "id": "CH-div", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-divider"],
    "meta": {"width": 24, "height": 2, "chartId": P["total"], "sliceName": ""}
}

# =====================================================
# ROW 8: KPI PREDIKSI (5 KPI)
# =====================================================
make_chart(P["total"], "Total Mahasiswa Diprediksi", 5, 8, "ROW-kpi-prediksi")
make_chart(P["tw"], "Prediksi Tepat Waktu", 5, 8, "ROW-kpi-prediksi")
make_chart(P["tl"], "Prediksi Terlambat", 5, 8, "ROW-kpi-prediksi")
make_chart(P["ptw"], "Persentase Tepat Waktu", 5, 8, "ROW-kpi-prediksi")
make_chart(P["ptl"], "Persentase Terlambat", 4, 8, "ROW-kpi-prediksi")
make_row("ROW-kpi-prediksi", ["CH-163", "CH-164", "CH-165", "CH-166", "CH-167"])

# =====================================================
# ROW 9: DISTRIBUSI PREDIKSI (2 charts)
# =====================================================
make_chart(P["dist"], "Distribusi Prediksi Kelulusan", 12, 14, "ROW-dist-prediksi")
make_chart(P["per_ang"], "Prediksi Kelulusan per Angkatan", 12, 14, "ROW-dist-prediksi")
make_row("ROW-dist-prediksi", ["CH-168", "CH-169"])

# =====================================================
# ROW 10: PROBABILITAS (2 charts)
# =====================================================
make_chart(P["label"], "Distribusi Label Data Training", 12, 14, "ROW-probabilitas")
make_chart(P["pct_ang"], "Persentase Prediksi per Angkatan", 12, 14, "ROW-probabilitas")
make_row("ROW-probabilitas", ["CH-172", "CH-170"])

# =====================================================
# ROW 11: DETAIL TABLE (full width)
# =====================================================
make_chart(P["detail"], "Detail Prediksi Mahasiswa", 24, 14, "ROW-detail")
make_row("ROW-detail", ["CH-171"])

# Save
dash.position_json = json.dumps(pos)
dash.dashboard_title = "Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa"
db.session.commit()

print("  Layout rebuilt with proper heights")

# =====================================================
# STEP 4: Validate all charts
# =====================================================
print("\n" + "=" * 60)
print("STEP 4: Validating all charts")
print("=" * 60)

all_ids = list(A.values()) + list(P.values())
all_pass = True
for cid in all_ids:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            print(f"  PASS  ID={cid:3d}  {s.viz_type:30s}  {s.slice_name}")
        else:
            print(f"  FAIL  ID={cid:3d}  {s.slice_name}  empty result")
            all_pass = False
    else:
        err = r.text[:100] if r.text else ""
        print(f"  FAIL  ID={cid:3d}  {s.slice_name}  HTTP {r.status_code} {err}")
        all_pass = False

print(f"\nALL CHARTS PASS: {all_pass}")
print(f"Dashboard URL: http://localhost:8088/superset/dashboard/6/")
print("=" * 60)
