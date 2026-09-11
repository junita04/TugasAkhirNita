"""
FINAL REVISION: Fix Dashboard 6 layout, rename charts (remove V2),
fix visualization types, and create professional layout.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice
from superset.models.dashboard import Dashboard

print("=" * 70)
print("FINAL REVISION: FIXING DASHBOARD 6")
print("=" * 70)

# =====================================================
# STEP 1: Rename all chart titles (remove V2)
# =====================================================
print("\nSTEP 1: Renaming chart titles (removing V2)...")

rename_map = {
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
    if s:
        old_name = s.slice_name
        s.slice_name = new_name
        db.session.commit()
        print(f"  ID={cid}: '{old_name}' -> '{new_name}'")

# =====================================================
# STEP 2: Fix chart 170 (pie -> table for better readability)
# =====================================================
print("\nSTEP 2: Fixing chart 170 (Persentase Prediksi per Angkatan)...")

s170 = db.session.query(Slice).get(170)
if s170:
    s170.viz_type = "table"
    s170.params = json.dumps({
        "all_columns": ["angkatan", "total_mahasiswa", "prediksi_tepat_waktu", "prediksi_terlambat", "persentase_tepat_waktu", "persentase_terlambat"],
        "order_by_cols": [],
        "row_limit": 100,
        "page_length": 0,
        "include_search": False,
    })
    s170.query_context = json.dumps({
        "datasource": {"id": 37, "type": "table"},
        "queries": [{"columns": ["angkatan", "total_mahasiswa", "prediksi_tepat_waktu", "prediksi_terlambat", "persentase_tepat_waktu", "persentase_terlambat"], "row_limit": 100}],
        "result_format": "json", "result_type": "full",
    })
    db.session.commit()
    print("  Fixed: pie -> table")

# =====================================================
# STEP 3: Rebuild Dashboard 6 layout
# =====================================================
print("\nSTEP 3: Rebuilding Dashboard 6 layout...")

dash = db.session.query(Dashboard).get(6)
if not dash:
    print("ERROR: Dashboard 6 not found!")
    sys.exit(1)

# Chart IDs
A = {  # Academic
    "total": 145, "aktif": 146, "lulus": 147, "tw": 148, "tl": 149,
    "ipk": 150, "ip": 151, "sks": 152, "angkatan": 153, "jk": 154,
    "status": 155, "kelulusan": 156, "ang_kel": 157, "ang_stat": 158,
    "ipk_ang": 159, "ip_ang": 160, "sks_ang": 161, "selisih_ang": 162,
}
P = {  # Prediction
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
            "ROW-profil",
            "ROW-kelulusan",
            "ROW-performa",
            "ROW-div-prediksi",
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

# =====================================================
# ROW 1: KPI AKADEMIK (compact, 5 columns)
# =====================================================
pos["ROW-kpi-akademik"] = {
    "type": "ROW", "id": "ROW-kpi-akademik",
    "children": ["CH-k1", "CH-k2", "CH-k3", "CH-k4", "CH-k5"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kpi_items = [
    ("CH-k1", A["total"], "Total Mahasiswa", 5),
    ("CH-k2", A["aktif"], "Mahasiswa Aktif", 5),
    ("CH-k3", A["lulus"], "Mahasiswa Lulus", 5),
    ("CH-k4", A["tw"], "Tepat Waktu", 5),
    ("CH-k5", A["tl"], "Terlambat", 4),
]
for cid, chart_key, name, w in kpi_items:
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kpi-akademik"],
        "meta": {"width": w, "height": 6, "chartId": chart_key, "sliceName": name}
    }

# =====================================================
# ROW 2: STATISTIK AKADEMIK (4 columns)
# =====================================================
pos["ROW-statistik"] = {
    "type": "ROW", "id": "ROW-statistik",
    "children": ["CH-s1", "CH-s2", "CH-s3", "CH-s4"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

stat_items = [
    ("CH-s1", A["ipk"], "Rata-rata IPK", 6),
    ("CH-s2", A["ip"], "Rata-rata IP", 6),
    ("CH-s3", A["sks"], "Rata-rata Total SKS", 6),
    ("CH-s4", A["selisih_ang"], "Rata-rata Selisih SKS per Angkatan", 6),
]
for cid, chart_key, name, w in stat_items:
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-statistik"],
        "meta": {"width": w, "height": 7, "chartId": chart_key, "sliceName": name}
    }

# =====================================================
# ROW 3: PROFIL MAHASISWA (3 columns)
# =====================================================
pos["ROW-profil"] = {
    "type": "ROW", "id": "ROW-profil",
    "children": ["CH-p1", "CH-p2", "CH-p3"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

profil_items = [
    ("CH-p1", A["angkatan"], "Jumlah Mahasiswa per Angkatan", 10),
    ("CH-p2", A["jk"], "Distribusi Jenis Kelamin", 7),
    ("CH-p3", A["status"], "Distribusi Status Mahasiswa", 7),
]
for cid, chart_key, name, w in profil_items:
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-profil"],
        "meta": {"width": w, "height": 8, "chartId": chart_key, "sliceName": name}
    }

# =====================================================
# ROW 4: STATUS KELULUSAN (3 columns)
# =====================================================
pos["ROW-kelulusan"] = {
    "type": "ROW", "id": "ROW-kelulusan",
    "children": ["CH-kl1", "CH-kl2", "CH-kl3"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kel_items = [
    ("CH-kl1", A["kelulusan"], "Status Kelulusan", 8),
    ("CH-kl2", A["ang_kel"], "Status Kelulusan per Angkatan", 8),
    ("CH-kl3", A["ang_stat"], "Status Mahasiswa per Angkatan", 8),
]
for cid, chart_key, name, w in kel_items:
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kelulusan"],
        "meta": {"width": w, "height": 8, "chartId": chart_key, "sliceName": name}
    }

# =====================================================
# ROW 5: PERFORMA AKADEMIK (2 columns)
# =====================================================
pos["ROW-performa"] = {
    "type": "ROW", "id": "ROW-performa",
    "children": ["CH-pf1", "CH-pf2"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

pos["CH-pf1"] = {
    "type": "CHART", "id": "CH-pf1", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-performa"],
    "meta": {"width": 12, "height": 7, "chartId": A["ipk_ang"], "sliceName": "Rata-rata IPK per Angkatan"}
}
pos["CH-pf2"] = {
    "type": "CHART", "id": "CH-pf2", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-performa"],
    "meta": {"width": 12, "height": 7, "chartId": A["ip_ang"], "sliceName": "Rata-rata IP per Angkatan"}
}

# =====================================================
# DIVIDER: PREDIKSI SECTION
# =====================================================
pos["ROW-div-prediksi"] = {
    "type": "ROW", "id": "ROW-div-prediksi",
    "children": ["CH-div1"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CH-div1"] = {
    "type": "CHART", "id": "CH-div1", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-div-prediksi"],
    "meta": {"width": 24, "height": 2, "chartId": P["total"], "sliceName": "--- Section: Prediksi Kelulusan ---"}
}

# =====================================================
# ROW 6: KPI PREDIKSI (5 columns)
# =====================================================
pos["ROW-kpi-prediksi"] = {
    "type": "ROW", "id": "ROW-kpi-prediksi",
    "children": ["CH-kp1", "CH-kp2", "CH-kp3", "CH-kp4", "CH-kp5"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kpi_pred = [
    ("CH-kp1", P["total"], "Total Diprediksi", 5),
    ("CH-kp2", P["tw"], "Prediksi Tepat Waktu", 5),
    ("CH-kp3", P["tl"], "Prediksi Terlambat", 5),
    ("CH-kp4", P["ptw"], "Persentase Tepat Waktu", 5),
    ("CH-kp5", P["ptl"], "Persentase Terlambat", 4),
]
for cid, chart_key, name, w in kpi_pred:
    pos[cid] = {
        "type": "CHART", "id": cid, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kpi-prediksi"],
        "meta": {"width": w, "height": 6, "chartId": chart_key, "sliceName": name}
    }

# =====================================================
# ROW 7: DISTRIBUSI PREDIKSI (2 columns)
# =====================================================
pos["ROW-dist-prediksi"] = {
    "type": "ROW", "id": "ROW-dist-prediksi",
    "children": ["CH-dp1", "CH-dp2"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

pos["CH-dp1"] = {
    "type": "CHART", "id": "CH-dp1", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-dist-prediksi"],
    "meta": {"width": 12, "height": 8, "chartId": P["dist"], "sliceName": "Distribusi Prediksi Kelulusan"}
}
pos["CH-dp2"] = {
    "type": "CHART", "id": "CH-dp2", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-dist-prediksi"],
    "meta": {"width": 12, "height": 8, "chartId": P["per_ang"], "sliceName": "Prediksi Kelulusan per Angkatan"}
}

# =====================================================
# ROW 8: PROBABILITAS & INSIGHT (2 columns)
# =====================================================
pos["ROW-probabilitas"] = {
    "type": "ROW", "id": "ROW-probabilitas",
    "children": ["CH-pr1", "CH-pr2"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

pos["CH-pr1"] = {
    "type": "CHART", "id": "CH-pr1", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-probabilitas"],
    "meta": {"width": 12, "height": 8, "chartId": P["label"], "sliceName": "Distribusi Label Data Training"}
}
pos["CH-pr2"] = {
    "type": "CHART", "id": "CH-pr2", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-probabilitas"],
    "meta": {"width": 12, "height": 8, "chartId": P["pct_ang"], "sliceName": "Persentase Prediksi per Angkatan"}
}

# =====================================================
# ROW 9: DETAIL MAHASISWA (full width)
# =====================================================
pos["ROW-detail"] = {
    "type": "ROW", "id": "ROW-detail",
    "children": ["CH-det1"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CH-det1"] = {
    "type": "CHART", "id": "CH-det1", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-detail"],
    "meta": {"width": 24, "height": 10, "chartId": P["detail"], "sliceName": "Detail Prediksi Mahasiswa"}
}

# Save layout
dash.position_json = json.dumps(pos)
dash.dashboard_title = "Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa"
db.session.commit()

print("  Layout rebuilt successfully")

# =====================================================
# STEP 4: Validate all charts
# =====================================================
print("\nSTEP 4: Validating all charts...")

import requests
SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

all_ids = list(A.values()) + list(P.values())
all_pass = True
for cid in all_ids:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            print(f"  PASS  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name}")
        else:
            print(f"  FAIL  ID={cid:3d}  {s.slice_name}  empty result")
            all_pass = False
    else:
        print(f"  FAIL  ID={cid:3d}  {s.slice_name}  HTTP {r.status_code}")
        all_pass = False

print(f"\nALL CHARTS PASS: {all_pass}")
print(f"Dashboard URL: http://localhost:8088/superset/dashboard/6/")
print("=" * 70)
