import requests
from requests.auth import HTTPBasicAuth

# Try different auth methods
for pwd in ["admin", "superset"]:
    for auth_type in ["basic", "cookie"]:
        try:
            if auth_type == "basic":
                r = requests.get("http://superset:8088/api/v1/database/", auth=HTTPBasicAuth("admin", pwd))
            else:
                # Session-based
                s = requests.Session()
                r = s.post("http://superset:8088/login/", data={"username": "admin", "password": pwd}, allow_redirects=False)
                r2 = s.get("http://superset:8088/api/v1/database/")
                print(f"Cookie '{pwd}': login={r.status_code} db={r2.status_code} {r2.text[:100]}")
                continue
            print(f"Basic '{pwd}': {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"Error {auth_type} '{pwd}': {e}")

# Check what Superset version
r = requests.get("http://superset:8088/health")
print(f"Health: {r.status_code} {r.text}")

# Check Superset config
r = requests.get("http://superset:8088/version")
print(f"Version: {r.status_code} {r.text[:100]}")

# Try the login endpoint with form data
s = requests.Session()
r = s.post("http://superset:8088/login/", data={"username": "admin", "password": "admin"})
print(f"Form login: {r.status_code} len={len(r.text)}")
if "dashboard" in r.text.lower() or "superset" in r.text.lower():
    print("  Seems logged in!")
    r2 = s.get("http://superset:8088/api/v1/database/")
    print(f"  DB list: {r2.status_code} {r2.text[:200]}")
