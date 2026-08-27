import requests
import json

session = requests.Session()

# Login
r = session.post('http://localhost:8088/api/v1/security/login', json={'username':'admin','password':'change-me','provider':'db'})
token = r.json().get('access_token','')
headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}

# Get CSRF token
r0 = session.get('http://localhost:8088/api/v1/security/csrf_token/', headers=headers)
csrf = r0.json().get('result','')
headers['X-CSRFToken'] = csrf
headers['Referer'] = 'http://localhost:8088'

# Test query on model_predictions
payload = {
    "database_id": 1,
    "sql": "SELECT prediksi, COUNT(*) as cnt FROM iceberg.gold.model_predictions GROUP BY prediksi",
    "runAsync": False
}
r2 = session.post('http://localhost:8088/api/v1/sqllab/execute/', headers=headers, json=payload)
data = r2.json()
print("Query result (model_predictions):")
if 'result' in data:
    for row in data['result'].get('data', []):
        print(f"  {row}")
else:
    print(json.dumps(data, indent=2)[:1000])

# Test query on prediction_by_angkatan
payload2 = {
    "database_id": 1,
    "sql": "SELECT * FROM iceberg.gold.prediction_by_angkatan ORDER BY angkatan",
    "runAsync": False
}
r3 = session.post('http://localhost:8088/api/v1/sqllab/execute/', headers=headers, json=payload2)
data2 = r3.json()
print()
print("Query result (prediction_by_angkatan):")
if 'result' in data2:
    for row in data2['result'].get('data', []):
        print(f"  {row}")
else:
    print(json.dumps(data2, indent=2)[:1000])

# Test query on model_metrics
payload3 = {
    "database_id": 1,
    "sql": "SELECT * FROM iceberg.gold.model_metrics",
    "runAsync": False
}
r4 = session.post('http://localhost:8088/api/v1/sqllab/execute/', headers=headers, json=payload3)
data3 = r4.json()
print()
print("Query result (model_metrics):")
if 'result' in data3:
    for row in data3['result'].get('data', []):
        print(f"  {row}")
else:
    print(json.dumps(data3, indent=2)[:1000])
