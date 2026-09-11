"""
REBUILD DASHBOARD 6 with CORRECT heights.
Dashboard 5 reference: KPI h=8 w=3, Charts h=50 w=6
Grid unit = ~8px, so h=50 = ~400px, h=8 = ~64px
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

# =====================================================
# STEP 1: Fix chart titles
# =====================================================
print("STEP 1: Renaming charts (no V2)...")

renames = {
    145: "Total Mahasiswa", 146: "Mahasiswa Aktif", 147: "Mahasiswa Lulus",
    148: "Tepat Waktu", 149: "Terlambat", 150: "Rata-rata IPK",
    151: "Rata-rata IP", 152: "Rata-rata Total SKS",
    153: "Distribusi Mahasiswa per Angkatan",
    154: "Distribusi Jenis Kelamin", 155: "Distribusi Status Mahasiswa",
    156: "Distribusi Status Kelulusan", 157: "Status Kelulusan per Angkatan",
    158: "Status Mahasiswa per Angkatan", 159: "Rata-rata IPK per Angkatan",
    160: "Rata-rata IP per Angkatan", 161: "Rata-rata Total SKS per Angkatan",
    162: "Rata-rata Selisih SKS per Angkatan",
    163: "Total Mahasiswa Diprediksi", 164: "Prediksi Tepat Waktu",
    165: "Prediksi Terlambat", 166: "Persentase Tepat Waktu",
    167: "Persentase Terlambat", 168: "Distribusi Prediksi Kelulusan",
    169: "Prediksi Kelulusan per Angkatan", 170: "Persentase Prediksi per Angkatan",
    171: "Detail Prediksi Mahasiswa", 172: "Distribusi Label Data Training",
}
for cid, name in renames.items():
    s = db.session.query(Slice).get(cid)
    if s and s.slice_name != name:
        print(f"  {cid}: '{s.slice_name}' -> '{name}'")
        s.slice_name = name
db.session.commit()

# =====================================================
# STEP 2: Fix echarts_bar charts
# =====================================================
print("\nSTEP 2: Fixing echarts_bar charts (159-162)...")
bar_fixes = [159, 160, 161, 162]
for cid in bar_fixes:
    s = db.session.query(Slice).get(cid)
    if s:
        s.viz_type = "echarts_timeseries_bar"
        params = json.loads(s.params) if s.params else {}
        params["x_axis"] = "angkatan"
        params["row_limit"] = 100
        s.params = json.dumps(params)
        s.query_context = json.dumps({
            "datasource": {"id": 27, "type": "table"},
            "queries": [{"columns": ["angkatan"], "row_limit": 100, "orderby": [["angkatan", True]]}],
            "result_format": "json", "result_type": "full",
        })
        print(f"  Chart {cid}: echarts_bar -> echarts_timeseries_bar")
db.session.commit()

# =====================================================
# STEP 3: Build new layout with correct heights
# =====================================================
print("\nSTEP 3: Building layout with correct heights...")
print("  Reference: KPI h=8 w=3, Charts h=50 w=6")

# Heights: KPI=8, Charts=50, Table=50
# Width: KPI=3 (4 per row), Charts=6 (2 per row), Table=12 (full)

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
            "ROW-profil-1", "ROW-profil-2",
            "ROW-performa-1", "ROW-performa-2",
            "ROW-divider",
            "ROW-kpi-prediksi",
            "ROW-dist-1",
            "ROW-dist-2",
            "ROW-detail",
        ],
        "parents": []
    },
    "HEADER_ID": {
        "type": "HEADER", "id": "HEADER_ID",
        "meta": {"text": "Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa"}
    },
}

def chart(chart_id, name, width, height, row_id):
    cid = f"CHART-{chart_id}"
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {"width": width, "height": height, "chartId": chart_id, "sliceName": name}
    }
    return cid

def row(row_id, chart_ids):
    pos[row_id] = {
        "type": "ROW", "id": row_id,
        "children": chart_ids,
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"}
    }

# =====================================================
# SECTION 1: KPI AKADEMIK (4 per row, h=8)
# =====================================================
chart(A["total"], "Total Mahasiswa", 3, 8, "ROW-kpi-akademik")
chart(A["aktif"], "Mahasiswa Aktif", 3, 8, "ROW-kpi-akademik")
chart(A["lulus"], "Mahasiswa Lulus", 3, 8, "ROW-kpi-akademik")
chart(A["tw"], "Tepat Waktu", 3, 8, "ROW-kpi-akademik")
row("ROW-kpi-akademik", ["CHART-145", "CHART-146", "CHART-147", "CHART-148"])

chart(A["tl"], "Terlambat", 3, 8, "ROW-statistik")
chart(A["ipk"], "Rata-rata IPK", 3, 8, "ROW-statistik")
chart(A["ip"], "Rata-rata IP", 3, 8, "ROW-statistik")
chart(A["sks"], "Rata-rata Total SKS", 3, 8, "ROW-statistik")
row("ROW-statistik", ["CHART-149", "CHART-150", "CHART-151", "CHART-152"])

# =====================================================
# SECTION 2: PROFIL MAHASISWA (2 per row, h=50)
# =====================================================
chart(A["jk"], "Distribusi Jenis Kelamin", 6, 50, "ROW-profil-1")
chart(A["status"], "Distribusi Status Mahasiswa", 6, 50, "ROW-profil-1")
row("ROW-profil-1", ["CHART-154", "CHART-155"])

chart(A["kelulusan"], "Distribusi Status Kelulusan", 6, 50, "ROW-profil-2")
chart(A["angkatan"], "Distribusi Mahasiswa per Angkatan", 6, 50, "ROW-profil-2")
row("ROW-profil-2", ["CHART-156", "CHART-153"])

# =====================================================
# SECTION 3: PERFORMA AKADEMIK (2 per row, h=50)
# =====================================================
chart(A["ipk_ang"], "Rata-rata IPK per Angkatan", 6, 50, "ROW-performa-1")
chart(A["ip_ang"], "Rata-rata IP per Angkatan", 6, 50, "ROW-performa-1")
row("ROW-performa-1", ["CHART-159", "CHART-160"])

chart(A["sks_ang"], "Rata-rata Total SKS per Angkatan", 6, 50, "ROW-performa-2")
chart(A["selisih_ang"], "Rata-rata Selisih SKS per Angkatan", 6, 50, "ROW-performa-2")
row("ROW-performa-2", ["CHART-161", "CHART-162"])

# =====================================================
# DIVIDER
# =====================================================
pos["ROW-divider"] = {
    "type": "ROW", "id": "ROW-divider", "children": ["CHART-div"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-div"] = {
    "type": "CHART", "id": "CHART-div", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-divider"],
    "meta": {"width": 24, "height": 1, "chartId": P["label"], "sliceName": ""}
}

# =====================================================
# SECTION 4: KPI PREDIKSI (4 per row, h=8)
# =====================================================
chart(P["total"], "Total Mahasiswa Diprediksi", 3, 8, "ROW-kpi-prediksi")
chart(P["tw"], "Prediksi Tepat Waktu", 3, 8, "ROW-kpi-prediksi")
chart(P["tl"], "Prediksi Terlambat", 3, 8, "ROW-kpi-prediksi")
chart(P["ptw"], "Persentase Tepat Waktu", 3, 8, "ROW-kpi-prediksi")
row("ROW-kpi-prediksi", ["CHART-163", "CHART-164", "CHART-165", "CHART-166"])

# =====================================================
# SECTION 5: DISTRIBUSI PREDIKSI (2 per row, h=50)
# =====================================================
chart(P["dist"], "Distribusi Prediksi Kelulusan", 6, 50, "ROW-dist-1")
chart(P["per_ang"], "Prediksi Kelulusan per Angkatan", 6, 50, "ROW-dist-1")
row("ROW-dist-1", ["CHART-168", "CHART-169"])

chart(P["label"], "Distribusi Label Data Training", 6, 50, "ROW-dist-2")
chart(P["pct_ang"], "Persentase Prediksi per Angkatan", 6, 50, "ROW-dist-2")
row("ROW-dist-2", ["CHART-172", "CHART-170"])

# =====================================================
# SECTION 6: DETAIL TABLE (full width, h=50)
# =====================================================
chart(P["detail"], "Detail Prediksi Mahasiswa", 12, 50, "ROW-detail")
row("ROW-detail", ["CHART-171"])

# Save
dash = db.session.query(Dashboard).get(6)
dash.position_json = json.dumps(pos)
dash.dashboard_title = "Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa"
db.session.commit()
print("  Layout saved")

# =====================================================
# STEP 4: Validate
# =====================================================
print("\nSTEP 4: Validating all charts...")
all_ids = list(A.values()) + list(P.values())
pass_count = 0
fail_count = 0
for cid in all_ids:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            print(f"  PASS  ID={cid:3d}  {s.viz_type:30s}  {s.slice_name}")
            pass_count += 1
        else:
            print(f"  FAIL  ID={cid:3d}  {s.slice_name}  empty")
            fail_count += 1
    else:
        print(f"  FAIL  ID={cid:3d}  {s.slice_name}  HTTP {r.status_code}")
        fail_count += 1

print(f"\nRESULT: {pass_count} PASS, {fail_count} FAIL")
print(f"URL: http://localhost:8088/superset/dashboard/6/")
