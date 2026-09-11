"""
Create unified dashboard combining Academic + Prediction data.
Dashboard 6: "Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa"

Reuses existing charts from Dashboard 5 (145-162) and Dashboard 3 (163-172).
Creates a few additional charts if needed.
Builds a professional layout with sections.
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
from superset.connectors.sqla.models import SqlaTable, Database

print("=" * 70)
print("CREATING UNIFIED DASHBOARD")
print("=" * 70)

# =====================================================
# Existing chart IDs
# =====================================================
# Dashboard 5 (Academic):
academic_charts = {
    "total_mahasiswa": 145,
    "mahasiswa_aktif": 146,
    "mahasiswa_lulus": 147,
    "tepat_waktu": 148,
    "terlambat": 149,
    "rata_rata_ipk": 150,
    "rata_rata_ip": 151,
    "rata_rata_sks": 152,
    "distribusi_angkatan": 153,
    "distribusi_jk": 154,
    "distribusi_status": 155,
    "status_kelulusan": 156,
    "angkatan_vs_kelulusan": 157,
    "angkatan_vs_status": 158,
    "ipk_per_angkatan": 159,
    "ip_per_angkatan": 160,
    "sks_per_angkatan": 161,
    "selisih_sks_per_angkatan": 162,
}

# Dashboard 3 V2 (Prediction):
prediction_charts = {
    "total_prediksi": 163,
    "tpw_prediksi": 164,
    "tl_prediksi": 165,
    "ptw_prediksi": 166,
    "ptl_prediksi": 167,
    "distribusi_prediksi": 168,
    "prediksi_per_angkatan": 169,
    "persentase_per_angkatan": 170,
    "detail_prediksi": 171,
    "distribusi_label_training": 172,
}

# Verify all charts exist
print("Verifying existing charts...")
all_ids = list(academic_charts.values()) + list(prediction_charts.values())
for cid in all_ids:
    s = db.session.query(Slice).get(cid)
    if s:
        print(f"  OK: ID={cid} {s.slice_name}")
    else:
        print(f"  MISSING: ID={cid}")

# =====================================================
# Create Dashboard 6
# =====================================================
print("\n" + "=" * 70)
print("CREATING DASHBOARD 6")
print("=" * 70)

dash = db.session.query(Dashboard).get(6)
if not dash:
    dash = Dashboard(
        dashboard_title="Dashboard Analitik Akademik dan Prediksi Kelulusan Mahasiswa",
        slug="dashboard-analitik-akademik-prediksi",
    )
    db.session.add(dash)
    db.session.commit()
    print(f"Created Dashboard 6 (ID={dash.id})")
else:
    print(f"Dashboard 6 already exists (ID={dash.id})")

# =====================================================
# Add ALL charts to dashboard
# =====================================================
print("\nAdding charts to dashboard...")
for cid in all_ids:
    s = db.session.query(Slice).get(cid)
    if s and s not in dash.slices:
        dash.slices.append(s)
        print(f"  Added: {s.slice_name}")
db.session.commit()

# =====================================================
# Build professional layout
# =====================================================
print("\nBuilding layout...")

pos = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {
        "type": "GRID", "id": "GRID_ID",
        "children": [
            "ROW-header",
            "ROW-filter",
            "ROW-kpi-akademik",
            "ROW-statistik-akademik",
            "ROW-profil-mahasiswa",
            "ROW-status-kelulusan",
            "ROW-performa-angkatan",
            "ROW-divider-prediksi",
            "ROW-kpi-prediksi",
            "ROW-distribusi-prediksi",
            "ROW-probabilitas",
            "ROW-insight",
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
# SECTION: HEADER
# =====================================================
pos["ROW-header"] = {
    "type": "ROW", "id": "ROW-header",
    "children": ["CHART-header-title"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-header-title"] = {
    "type": "CHART", "id": "CHART-header-title",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-header"],
    "meta": {
        "width": 24, "height": 4,
        "chartId": academic_charts["total_mahasiswa"],
        "sliceName": "Dashboard Header",
    }
}

# =====================================================
# SECTION: KPI AKADEMIK (ROW 1)
# =====================================================
pos["ROW-kpi-akademik"] = {
    "type": "ROW", "id": "ROW-kpi-akademik",
    "children": ["CHART-kpi1", "CHART-kpi2", "CHART-kpi3", "CHART-kpi4", "CHART-kpi5"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kpi_mapping = [
    ("CHART-kpi1", academic_charts["total_mahasiswa"], "Total Mahasiswa", 5),
    ("CHART-kpi2", academic_charts["mahasiswa_aktif"], "Mahasiswa Aktif", 5),
    ("CHART-kpi3", academic_charts["mahasiswa_lulus"], "Mahasiswa Lulus", 5),
    ("CHART-kpi4", academic_charts["tepat_waktu"], "Tepat Waktu", 5),
    ("CHART-kpi5", academic_charts["terlambat"], "Terlambat", 4),
]
for chart_id, chart_key, chart_name, width in kpi_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kpi-akademik"],
        "meta": {"width": width, "height": 7, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# SECTION: STATISTIK AKADEMIK (ROW 2)
# =====================================================
pos["ROW-statistik-akademik"] = {
    "type": "ROW", "id": "ROW-statistik-akademik",
    "children": ["CHART-stat1", "CHART-stat2", "CHART-stat3", "CHART-stat4"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

stat_mapping = [
    ("CHART-stat1", academic_charts["rata_rata_ipk"], "Rata-rata IPK", 6),
    ("CHART-stat2", academic_charts["rata_rata_ip"], "Rata-rata IP", 6),
    ("CHART-stat3", academic_charts["rata_rata_sks"], "Rata-rata Total SKS", 6),
    ("CHART-stat4", academic_charts["selisih_sks_per_angkatan"], "Selisih SKS per Angkatan", 6),
]
for chart_id, chart_key, chart_name, width in stat_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-statistik-akademik"],
        "meta": {"width": width, "height": 8, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# SECTION: PROFIL MAHASISWA (ROW 3)
# =====================================================
pos["ROW-profil-mahasiswa"] = {
    "type": "ROW", "id": "ROW-profil-mahasiswa",
    "children": ["CHART-profil1", "CHART-profil2", "CHART-profil3"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

profil_mapping = [
    ("CHART-profil1", academic_charts["distribusi_angkatan"], "Distribusi Angkatan", 10),
    ("CHART-profil2", academic_charts["distribusi_jk"], "Distribusi Jenis Kelamin", 7),
    ("CHART-profil3", academic_charts["distribusi_status"], "Distribusi Status Mahasiswa", 7),
]
for chart_id, chart_key, chart_name, width in profil_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-profil-mahasiswa"],
        "meta": {"width": width, "height": 9, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# SECTION: STATUS KELULUSAN (ROW 4)
# =====================================================
pos["ROW-status-kelulusan"] = {
    "type": "ROW", "id": "ROW-status-kelulusan",
    "children": ["CHART-kel1", "CHART-kel2", "CHART-kel3"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kel_mapping = [
    ("CHART-kel1", academic_charts["status_kelulusan"], "Status Kelulusan", 8),
    ("CHART-kel2", academic_charts["angkatan_vs_kelulusan"], "Angkatan vs Kelulusan", 8),
    ("CHART-kel3", academic_charts["angkatan_vs_status"], "Angkatan vs Status Mahasiswa", 8),
]
for chart_id, chart_key, chart_name, width in kel_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-status-kelulusan"],
        "meta": {"width": width, "height": 9, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# SECTION: PERFORMA AKADEMIK PER ANGKATAN (ROW 5)
# =====================================================
pos["ROW-performa-angkatan"] = {
    "type": "ROW", "id": "ROW-performa-angkatan",
    "children": ["CHART-perf1", "CHART-perf2"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

perf_mapping = [
    ("CHART-perf1", academic_charts["ipk_per_angkatan"], "Rata-rata IPK per Angkatan", 12),
    ("CHART-perf2", academic_charts["ip_per_angkatan"], "Rata-rata IP per Angkatan", 12),
]
for chart_id, chart_key, chart_name, width in perf_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-performa-angkatan"],
        "meta": {"width": width, "height": 8, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# DIVIDER: HASIL PREDIKSI MACHINE LEARNING
# =====================================================
pos["ROW-divider-prediksi"] = {
    "type": "ROW", "id": "ROW-divider-prediksi",
    "children": ["CHART-divider"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-divider"] = {
    "type": "CHART", "id": "CHART-divider",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-divider-prediksi"],
    "meta": {
        "width": 24, "height": 3,
        "chartId": prediction_charts["total_prediksi"],
        "sliceName": "Divider: Hasil Prediksi ML",
    }
}

# =====================================================
# SECTION: KPI PREDIKSI (ROW 7)
# =====================================================
pos["ROW-kpi-prediksi"] = {
    "type": "ROW", "id": "ROW-kpi-prediksi",
    "children": ["CHART-kp1", "CHART-kp2", "CHART-kp3", "CHART-kp4", "CHART-kp5"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kpi_pred_mapping = [
    ("CHART-kp1", prediction_charts["total_prediksi"], "Total Diprediksi", 5),
    ("CHART-kp2", prediction_charts["tpw_prediksi"], "Prediksi Tepat Waktu", 5),
    ("CHART-kp3", prediction_charts["tl_prediksi"], "Prediksi Terlambat", 5),
    ("CHART-kp4", prediction_charts["ptw_prediksi"], "% Tepat Waktu", 5),
    ("CHART-kp5", prediction_charts["ptl_prediksi"], "% Terlambat", 4),
]
for chart_id, chart_key, chart_name, width in kpi_pred_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kpi-prediksi"],
        "meta": {"width": width, "height": 7, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# SECTION: DISTRIBUSI PREDIKSI (ROW 8)
# =====================================================
pos["ROW-distribusi-prediksi"] = {
    "type": "ROW", "id": "ROW-distribusi-prediksi",
    "children": ["CHART-dist1", "CHART-dist2", "CHART-dist3"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

dist_mapping = [
    ("CHART-dist1", prediction_charts["distribusi_prediksi"], "Distribusi Prediksi", 8),
    ("CHART-dist2", prediction_charts["prediksi_per_angkatan"], "Prediksi per Angkatan", 8),
    ("CHART-dist3", prediction_charts["persentase_per_angkatan"], "Persentase per Angkatan", 8),
]
for chart_id, chart_key, chart_name, width in dist_mapping:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-distribusi-prediksi"],
        "meta": {"width": width, "height": 9, "chartId": chart_key, "sliceName": chart_name}
    }

# =====================================================
# SECTION: PROBABILITAS (ROW 9)
# =====================================================
pos["ROW-probabilitas"] = {
    "type": "ROW", "id": "ROW-probabilitas",
    "children": ["CHART-prob1"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-prob1"] = {
    "type": "CHART", "id": "CHART-prob1",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-probabilitas"],
    "meta": {
        "width": 24, "height": 9,
        "chartId": prediction_charts["distribusi_label_training"],
        "sliceName": "Distribusi Label Training",
    }
}

# =====================================================
# SECTION: INSIGHT (ROW 10)
# =====================================================
pos["ROW-insight"] = {
    "type": "ROW", "id": "ROW-insight",
    "children": ["CHART-insight1"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-insight1"] = {
    "type": "CHART", "id": "CHART-insight1",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-insight"],
    "meta": {
        "width": 24, "height": 8,
        "chartId": prediction_charts["persentase_per_angkatan"],
        "sliceName": "Insight: Persentase Prediksi per Angkatan",
    }
}

# =====================================================
# SECTION: DETAIL MAHASISWA (ROW 11)
# =====================================================
pos["ROW-detail"] = {
    "type": "ROW", "id": "ROW-detail",
    "children": ["CHART-detail"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-detail"] = {
    "type": "CHART", "id": "CHART-detail",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-detail"],
    "meta": {
        "width": 24, "height": 12,
        "chartId": prediction_charts["detail_prediksi"],
        "sliceName": "Detail Prediksi Mahasiswa",
    }
}

# =====================================================
# Save layout
# =====================================================
dash.position_json = json.dumps(pos)
db.session.commit()

print(f"Dashboard 6 updated with {len(dash.slices)} charts")
print(f"URL: http://localhost:8088/superset/dashboard/6/")

# =====================================================
# Final validation
# =====================================================
print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

import requests
SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

all_pass = True
for cid in all_ids:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            row_count = len(data["result"][0].get("data", []))
            category = "AKADEMIK" if cid in academic_charts.values() else "PREDIKSI"
            print(f"  PASS  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:40s}  [{category}]")
        else:
            print(f"  FAIL  ID={cid:3d}  {s.slice_name:40s}  empty result")
            all_pass = False
    else:
        print(f"  FAIL  ID={cid:3d}  {s.slice_name:40s}  HTTP {r.status_code}")
        all_pass = False

print(f"\nALL CHARTS PASS: {all_pass}")
print(f"Total charts: {len(all_ids)}")
print(f"Dashboard URL: http://localhost:8088/superset/dashboard/6/")
print("=" * 70)
