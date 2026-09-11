"""
Validate all 8 KPI charts after restore.
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

all_kpis = [
    (145, "Total Mahasiswa", "COUNT(*)", "Total Mahasiswa", 32703),
    (146, "Mahasiswa Aktif",
     "COUNT(CASE WHEN status_mahasiswa = 'AKTIF' THEN 1 END)", "Mahasiswa Aktif", 14945),
    (147, "Mahasiswa Lulus",
     "COUNT(CASE WHEN status_mahasiswa = 'Lulus' THEN 1 END)", "Mahasiswa Lulus", 13328),
    (148, "Mahasiswa Tepat Waktu",
     "COUNT(CASE WHEN status_kelulusan = 'Tepat Waktu' THEN 1 END)", "Mahasiswa Tepat Waktu", 3192),
    (149, "Mahasiswa Terlambat",
     "COUNT(CASE WHEN status_kelulusan = 'Terlambat' THEN 1 END)", "Mahasiswa Terlambat", 12580),
    (150, "Rata-rata IPK", "ROUND(AVG(ipk), 2)", "Rata-rata IPK", 2.64),
    (151, "Rata-rata IP", "ROUND(AVG(ip), 2)", "Rata-rata IP", 2.98),
    (152, "Rata-rata Total SKS", "ROUND(AVG(total_sks), 1)", "Rata-rata Total SKS", 114.8),
]

pass_count = 0
fail_count = 0

for cid, title, sql_expr, label, expected in all_kpis:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    
    vt = s.viz_type if s else "N/A"
    ds = s.datasource_id if s else "N/A"
    
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            status = q.get('status', 'unknown')
            val = list(d[0].values())[0] if d else "N/A"
            if status == 'success':
                pass_count += 1
                print(f"  PASS  ID={cid:3d} {title:35s} viz={vt:20s} ds={ds:3d} val={val}")
            else:
                fail_count += 1
                print(f"  WARN  ID={cid:3d} {title:35s} viz={vt:20s} ds={ds:3d} status={status}")
        else:
            fail_count += 1
            print(f"  FAIL  ID={cid:3d} {title:35s} viz={vt:20s} ds={ds:3d} empty")
    else:
        fail_count += 1
        err = r.text[:100] if r.text else ""
        print(f"  FAIL  ID={cid:3d} {title:35s} HTTP {r.status_code} {err}")

print(f"\n=== RESULT: {pass_count} PASS, {fail_count} FAIL ===")
print(f"URL: http://localhost:8088/superset/dashboard/6/")
