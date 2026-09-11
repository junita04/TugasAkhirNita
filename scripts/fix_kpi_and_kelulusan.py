"""
FIX: 1) KPI font size to maximum (1.0) 2) Chart 156 pie config
"""
import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.models.slice import Slice

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# =====================================================
# FIX 1: KPI font size to 1.0 (maximum)
# =====================================================
print("FIX 1: Increasing KPI font sizes to 1.0...")

kpi_ids = [145, 146, 147, 148, 149, 150, 151, 152, 163, 164, 165, 166, 167]
for cid in kpi_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    params = json.loads(s.params) if s.params else {}
    params['header_font_size'] = 1.0
    params['subheader_font_size'] = 0.3
    s.params = json.dumps(params)
    print(f"  ID={cid:3d} {s.slice_name:35s} header=1.0 sub=0.3")
db.session.commit()

# =====================================================
# FIX 2: Chart 156 - Distribusi Status Kelulusan
# Error: "Cannot read properties of undefined (reading 'label')"
# Cause: CASE WHEN in metric causes rendering issue
# Fix: Use groupby with simple COUNT metric
# =====================================================
print("\nFIX 2: Fixing chart 156 (Distribusi Status Kelulusan)...")

s156 = db.session.query(Slice).get(156)
if s156:
    # Use simple groupby with CASE WHEN in a subquery approach
    # The pie chart needs groupby + metric, not complex metric
    params = {
        "viz_type": "pie",
        "groupby": [{
            "expressionType": "SQL",
            "sqlExpression": "CASE WHEN status_kelulusan IS NULL OR status_kelulusan = '' THEN 'Belum Lulus' ELSE status_kelulusan END",
            "label": "Status Kelulusan"
        }],
        "metric": {
            "expressionType": "SQL",
            "sqlExpression": "COUNT(*)",
            "label": "Jumlah"
        },
        "row_limit": 100,
        "sort_by_metric": True,
        "innerRadius": 30,
        "outerRadius": 70,
        "show_labels": True,
        "labelsOutside": True,
        "label_type": "key_percent",
        "show_legend": True,
    }
    
    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "columns": [{
                "expressionType": "SQL",
                "sqlExpression": "CASE WHEN status_kelulusan IS NULL OR status_kelulusan = '' THEN 'Belum Lulus' ELSE status_kelulusan END",
                "label": "Status Kelulusan"
            }],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
            "row_limit": 100,
            "orderby": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}, False],
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s156.params = json.dumps(params)
    s156.query_context = json.dumps(qc)
    print("  Fixed: using groupby + simple COUNT metric")

# Also fix chart 154 (Distribusi Jenis Kelamin) and 155 (Distribusi Status Mahasiswa)
# to use same stable pie config pattern
for cid in [154, 155]:
    s = db.session.query(Slice).get(cid)
    if s:
        params = json.loads(s.params) if s.params else {}
        params['sort_by_metric'] = True
        params['show_legend'] = True
        params['show_labels'] = True
        params['label_type'] = 'key_percent'
        s.params = json.dumps(params)
        print(f"  ID={cid} {s.slice_name}: updated pie config")

# Fix chart 168 (Distribusi Prediksi Kelulusan) and 172 (Distribusi Label Data Training)
for cid in [168, 172]:
    s = db.session.query(Slice).get(cid)
    if s:
        params = json.loads(s.params) if s.params else {}
        params['sort_by_metric'] = True
        params['show_legend'] = True
        params['show_labels'] = True
        params['label_type'] = 'key_percent'
        s.params = json.dumps(params)
        print(f"  ID={cid} {s.slice_name}: updated pie config")

db.session.commit()

# =====================================================
# VALIDATE
# =====================================================
print("\n=== VALIDATION ===")

# Test KPI font sizes
for cid in [145, 146, 147]:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    params = json.loads(s.params) if s.params else {}
    print(f"  ID={cid} {s.slice_name}: header_font={params.get('header_font_size')} PASS={r.status_code==200}")

# Test chart 156
r = requests.get(f'{SUPERSET}/api/v1/chart/156/data/', headers=headers, params={'force': 'true'})
s = db.session.query(Slice).get(156)
print(f"  ID=156 {s.slice_name}: HTTP={r.status_code} PASS={r.status_code==200}")
if r.status_code == 200:
    data = r.json()
    if 'result' in data and data['result']:
        for q in data['result']:
            d = q.get('data', [])
            print(f"    Rows: {len(d)}, Sample: {d[:3]}")

# Full validation
print("\n=== FULL CHART VALIDATION ===")
all_ids = list(range(145, 173))
pass_count = 0
fail_count = 0
for cid in all_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and isinstance(data['result'], list) and len(data['result']) > 0:
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
