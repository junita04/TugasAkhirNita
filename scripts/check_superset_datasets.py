import requests
r = requests.post('http://localhost:8088/api/v1/security/login', json={'username':'admin','password':'change-me','provider':'db'})
token = r.json().get('access_token','')
headers = {'Authorization': 'Bearer ' + token}
r2 = requests.get('http://localhost:8088/api/v1/dataset/', headers=headers)
data = r2.json()
count = data.get('count', 0)
print('Datasets: ' + str(count))
for d in data.get('result', []):
    print('  ' + d['table_name'] + ' (schema=' + str(d.get('schema','')) + ')')
