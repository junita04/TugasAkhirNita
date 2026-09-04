import requests
import json

SUPERSET_URL = "http://superset:8088"

# Try login with different passwords
for pwd in ["admin", "superset"]:
    try:
        r = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json={
            "username": "admin",
            "password": pwd,
            "provider": "db",
            "refresh": True
        })
        print(f"Password '{pwd}': {r.status_code} {r.text[:100]}")
        if r.status_code == 200:
            token = r.json()["access_token"]
            # Test authenticated endpoint
            headers = {"Authorization": f"Bearer {token}"}
            r2 = requests.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers)
            print(f"  Databases: {r2.status_code} {r2.text[:200]}")
            break
    except Exception as e:
        print(f"Password '{pwd}': ERROR {e}")
