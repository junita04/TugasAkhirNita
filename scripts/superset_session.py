import requests

s = requests.Session()
# Login via form
r = s.post('http://superset:8088/login/', data={'username': 'admin', 'password': 'admin'})
print('Form login status:', r.status_code)

# Try to get CSRF token
r2 = s.get('http://superset:8088/superset/csrf_token/')
print('CSRF:', r2.status_code, len(r2.text))

# Try to access the API with session cookies
r3 = s.get('http://superset:8088/api/v1/database/')
print('DB API:', r3.status_code, r3.text[:200])
