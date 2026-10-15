import requests
import json

# Login to Superset
login_url = "http://localhost:8088/login/"
login_data = {"username": "admin", "password": "admin"}

session = requests.Session()
session.get(login_url)

# Get CSRF token
csrf_url = "http://localhost:8088/api/v1/security/csrf_token/"
csrf_resp = session.get(csrf_url)
csrf_token = csrf_resp.json().get("result", "")

# List databases
db_url = "http://localhost:8088/api/v1/database/"
headers = {
    "Authorization": "Bearer ",
    "X-CSRFToken": csrf_token,
    "Content-Type": "application/json"
}

# Try with session cookie auth
resp = session.get(db_url)
print("Databases response:", resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    for db in data.get("result", []):
        print(f"  DB: {db.get('database_name')} (id={db.get('id')})")
