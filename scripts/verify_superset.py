import requests

s = requests.Session()
r = s.post('http://localhost:8088/api/v1/security/login', json={'username':'admin','password':'change-me','provider':'db'})
token = r.json()['access_token']
h = {'Authorization': 'Bearer ' + token}
r0 = s.get('http://localhost:8088/api/v1/security/csrf_token/', headers=h)
csrf = r0.json()['result']
h['X-CSRFToken'] = csrf
h['Referer'] = 'http://localhost:8088'

# Check dashboard
r = s.get('http://localhost:8088/api/v1/dashboard/1', headers=h)
d = r.json()['result']
print('Dashboard:', d['dashboard_title'])
print('Published:', d['published'])
print('Slug:', d.get('slug',''))

# Check charts
r2 = s.get('http://localhost:8088/api/v1/chart/?q=(page_size:50)', headers=h)
charts = r2.json()['result']
print('Total charts:', len(charts))
for c in charts:
    print('  id=' + str(c['id']) + ' ' + c['slice_name'] + ' (type=' + c['viz_type'] + ')')

# Check datasets
r3 = s.get('http://localhost:8088/api/v1/dataset/?q=(page_size:50)', headers=h)
datasets = r3.json()['result']
print('Total datasets:', len(datasets))
for ds in datasets:
    print('  id=' + str(ds['id']) + ' ' + ds['table_name'] + ' (schema=' + str(ds.get('schema','')) + ')')
