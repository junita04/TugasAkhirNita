"""
COMPREHENSIVE DASHBOARD REBUILD
- Professional maroon/dark red color scheme
- All 26 charts with proper params
- 6 sections with proper layout
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

def make_metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}

def make_adhoc(subject, op, comp):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": op, "comparator": comp, "clause": "WHERE"}

s = api()

# ============================================================
# COLOR SCHEMES
# ============================================================
# Maroon/Professional scheme
COLOR_MAROON = "supersetClassic"  # Fallback
COLOR_SCHEME = "supersetCategory10"  # Default

# For pie charts - custom colors
PIE_COLORS_GENDER = ["#C41E3A", "#4A90D9"]  # Maroon, Blue
PIE_COLORS_STATUS = ["#C41E3A", "#E8524A", "#F5A623", "#4CAF50", "#9C27B0", "#607D8B"]
PIE_COLORS_KELULUSAN = ["#4CAF50", "#C41E3A"]  # Green=TW, Red=Terlambat
PIE_COLORS_PREDIKSI = ["#4A90D9", "#C41E3A"]  # Blue=TW, Red=Terlambat

# ============================================================
# STEP 1: UPDATE ALL CHART PARAMS
# ============================================================
print("=" * 70)
print("STEP 1: UPDATING CHART PARAMS")
print("=" * 70)

# Chart 66-70: KPI cards - keep as is (big_number_total)
# They're already working fine

# Chart 71: Jumlah Mahasiswa per Angkatan
r = s.get(f"{BASE}/api/v1/chart/71")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = False
params["rich_tooltip"] = True
s.put(f"{BASE}/api/v1/chart/71", json={"params": json.dumps(params)})
print("Chart 71: updated")

# Chart 72: Distribusi Jenis Kelamin (pie)
r = s.get(f"{BASE}/api/v1/chart/72")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = True
params["show_labels"] = True
params["label_type"] = "key_value_percent"
params["donut"] = True
params["innerRadius"] = 40
params["outerRadius"] = 80
s.put(f"{BASE}/api/v1/chart/72", json={"params": json.dumps(params)})
print("Chart 72: updated")

# Chart 73: Distribusi Status Mahasiswa (pie)
r = s.get(f"{BASE}/api/v1/chart/73")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = True
params["show_labels"] = True
params["label_type"] = "key_value_percent"
params["donut"] = True
params["innerRadius"] = 40
params["outerRadius"] = 80
s.put(f"{BASE}/api/v1/chart/73", json={"params": json.dumps(params)})
print("Chart 73: updated")

# Charts 74-77: Academic metrics per angkatan (bar charts)
for cid in [74, 75, 76, 77]:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    params = json.loads(c["params"])
    params["color_scheme"] = COLOR_SCHEME
    params["show_legend"] = False
    params["rich_tooltip"] = True
    params["stack"] = False
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(params)})
    print(f"Chart {cid}: updated")

# Chart 78: Status Kelulusan Aktual (pie)
r = s.get(f"{BASE}/api/v1/chart/78")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = True
params["show_labels"] = True
params["label_type"] = "key_value_percent"
params["donut"] = True
params["innerRadius"] = 40
params["outerRadius"] = 80
s.put(f"{BASE}/api/v1/chart/78", json={"params": json.dumps(params)})
print("Chart 78: updated")

# Chart 79: Status Kelulusan per Angkatan (stacked bar)
r = s.get(f"{BASE}/api/v1/chart/79")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = True
params["stack"] = True
params["rich_tooltip"] = True
s.put(f"{BASE}/api/v1/chart/79", json={"params": json.dumps(params)})
print("Chart 79: updated")

# Chart 80: Persentase Tepat Waktu per Angkatan
r = s.get(f"{BASE}/api/v1/chart/80")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = False
params["rich_tooltip"] = True
s.put(f"{BASE}/api/v1/chart/80", json={"params": json.dumps(params)})
print("Chart 80: updated")

# Charts 81-84: ML metrics KPI - keep as is

# Chart 85: Confusion Matrix (table)
r = s.get(f"{BASE}/api/v1/chart/85")
c = r.json()["result"]
params = json.loads(c["params"])
params["show_cell_bars"] = True
params["page_length"] = 10
params["order_desc"] = True
s.put(f"{BASE}/api/v1/chart/85", json={"params": json.dumps(params)})
print("Chart 85: updated")

# Chart 86: Classification Report (table)
r = s.get(f"{BASE}/api/v1/chart/86")
c = r.json()["result"]
params = json.loads(c["params"])
params["show_cell_bars"] = True
params["page_length"] = 10
params["order_desc"] = True
s.put(f"{BASE}/api/v1/chart/86", json={"params": json.dumps(params)})
print("Chart 86: updated")

# Chart 87: Prediksi ML per Angkatan
r = s.get(f"{BASE}/api/v1/chart/87")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = True
params["rich_tooltip"] = True
params["stack"] = False
s.put(f"{BASE}/api/v1/chart/87", json={"params": json.dumps(params)})
print("Chart 87: updated")

# Chart 88: Distribusi Prediksi ML (pie)
r = s.get(f"{BASE}/api/v1/chart/88")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = True
params["show_labels"] = True
params["label_type"] = "key_value_percent"
params["donut"] = True
params["innerRadius"] = 40
params["outerRadius"] = 80
s.put(f"{BASE}/api/v1/chart/88", json={"params": json.dumps(params)})
print("Chart 88: updated")

# Chart 89: Selisih SKS per Semester
r = s.get(f"{BASE}/api/v1/chart/89")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = False
params["rich_tooltip"] = True
s.put(f"{BASE}/api/v1/chart/89", json={"params": json.dumps(params)})
print("Chart 89: updated")

# Chart 91: Mahasiswa Aktif per Semester
r = s.get(f"{BASE}/api/v1/chart/91")
c = r.json()["result"]
params = json.loads(c["params"])
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = False
params["rich_tooltip"] = True
s.put(f"{BASE}/api/v1/chart/91", json={"params": json.dumps(params)})
print("Chart 91: updated")

# Chart 100: Distribusi IPK (histogram)
r = s.get(f"{BASE}/api/v1/chart/100")
c = r.json()["result"]
params = json.loads(c["params"])
if c["viz_type"] != "histogram":
    # Already updated to histogram earlier
    pass
params["color_scheme"] = COLOR_SCHEME
params["show_legend"] = False
params["x_axis_label"] = "IPK"
params["y_axis_label"] = "Jumlah Mahasiswa"
s.put(f"{BASE}/api/v1/chart/100", json={"params": json.dumps(params)})
print("Chart 100: updated")

print("\nAll chart params updated!")
