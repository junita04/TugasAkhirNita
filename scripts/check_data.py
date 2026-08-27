"""
Check classification report and confusion matrix data
"""
import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s

s = api()

# Classification Report data
print("=== CLASSIFICATION REPORT ===")
r = s.get(f"{BASE}/api/v1/chart/86")
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    for row in data["result"][0].get("data", []):
        print(f"  {row}")

print("\n=== CONFUSION MATRIX ===")
r = s.get(f"{BASE}/api/v1/chart/85")
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    for row in data["result"][0].get("data", []):
        print(f"  {row}")

print("\n=== PREDICTION BY ANGKATAN ===")
r = s.get(f"{BASE}/api/v1/chart/87")
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    for row in data["result"][0].get("data", []):
        print(f"  {row}")

print("\n=== MODEL METRICS ===")
r = s.get(f"{BASE}/api/v1/chart/81")
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    for row in data["result"][0].get("data", []):
        print(f"  {row}")
