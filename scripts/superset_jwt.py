import requests
import json

s = requests.Session()

# First login via form to get CSRF
r = s.post('http://superset:8088/login/', data={'username': 'admin', 'password': 'admin'})
print('Form login:', r.status_code)

# Get CSRF token
csrf_resp = s.get('http://superset:8088/superset/csrf_token/')
csrf_token = csrf_resp.text if csrf_resp.status_code == 200 else None
print('CSRF token length:', len(csrf_resp.text) if csrf_resp else 0)

# Try JWT login
login_data = {
    "username": "admin",
    "password": "admin",
    "provider": "db",
    "refresh": True
}
r2 = s.post('http://superset:8088/api/v1/security/login', json=login_data)
print('JWT login:', r2.status_code, r2.text[:200])

if r2.status_code == 200:
    token = r2.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    r3 = requests.get('http://superset:8088/api/v1/database/', headers=headers)
    print('DB with JWT:', r3.status_code, r3.text[:200])
else:
    # Try with CSRF header
    if csrf_token:
        headers = {"X-CSRFToken": csrf_token, "Referer": "http://superset:8088/"}
        r3 = s.get('http://superset:8088/api/v1/database/', headers=headers)
        print('DB with CSRF:', r3.status_code, r3.text[:200])

# Check superset version info
r4 = s.get('http://superset:8088/health')
print('Health:', r4.status_code, r4.text)

# Check if admin user exists by trying to access user API
r5 = s.get('http://superset:8088/api/v1/security/guest_token/', headers={"X-CSRFToken": csrf_token, "Referer": "http://superset:8088/"} if csrf_token else {})
print('Guest token:', r5.status_code, r5.text[:200])
