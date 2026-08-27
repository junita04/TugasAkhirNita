import requests
import json

s = requests.Session()
r = s.post('http://localhost:8088/api/v1/security/login', json={'username':'admin','password':'change-me','provider':'db'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}
r0 = s.get('http://localhost:8088/api/v1/security/csrf_token/', headers=h)
csrf = r0.json()['result']
h['X-CSRFToken'] = csrf
h['Referer'] = 'http://localhost:8088'

# Test key charts by running their data queries
test_queries = [
    ("Total Mahasiswa", "SELECT COUNT(*) as total FROM iceberg.gold.data_referensi_mahasiswa"),
    ("Mahasiswa Aktif", "SELECT COUNT(*) as total FROM iceberg.gold.data_referensi_mahasiswa WHERE status_mahasiswa='AKTIF'"),
    ("Mahasiswa Lulus", "SELECT COUNT(*) as total FROM iceberg.gold.data_referensi_mahasiswa WHERE status_mahasiswa='Lulus'"),
    ("Tepat Waktu", "SELECT COUNT(*) as total FROM iceberg.gold.data_referensi_mahasiswa WHERE status_kelulusan='Tepat Waktu'"),
    ("Terlambat", "SELECT COUNT(*) as total FROM iceberg.gold.data_referensi_mahasiswa WHERE status_kelulusan='Terlambat'"),
    ("Model Accuracy", "SELECT test_accuracy FROM iceberg.gold.model_metrics"),
    ("Prediction by Angkatan", "SELECT angkatan, prediksi_tepat_waktu, prediksi_terlambat FROM iceberg.gold.prediction_by_angkatan ORDER BY angkatan"),
]

print("Chart Data Validation:")
print("=" * 60)
for name, sql in test_queries:
    payload = {"database_id": 1, "sql": sql, "runAsync": False}
    r2 = s.post('http://localhost:8088/api/v1/sqllab/execute/', headers=h, json=payload)
    data = r2.json()
    if 'result' in data:
        rows = data['result'].get('data', [])
        print(f"  {name}: {rows}")
    else:
        print(f"  {name}: ERROR - {json.dumps(data)[:200]}")

print()
print("Dashboard URL: http://localhost:8088/superset/dashboard/1/")
