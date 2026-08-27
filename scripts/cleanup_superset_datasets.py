import requests
import json

r = requests.post('http://localhost:8088/api/v1/security/login', json={'username':'admin','password':'change-me','provider':'db'})
token = r.json().get('access_token','')
headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}

# List all datasets
r2 = requests.get('http://localhost:8088/api/v1/dataset/?q=(page_size:100)', headers=headers)
data = r2.json()
datasets = data.get('result', [])
print('All datasets:')
for d in datasets:
    print(f'  id={d["id"]} {d["table_name"]} (schema={d.get("schema","")})')

# Delete old datasets (gold_mahasiswa, gold_program_studi, gold_kurikulum, prediction_result)
old_tables = ['gold_mahasiswa', 'gold_program_studi', 'gold_kurikulum', 'prediction_result']
for d in datasets:
    if d['table_name'] in old_tables:
        print(f'Deleting old dataset: {d["table_name"]} (id={d["id"]})')
        r3 = requests.delete(f'http://localhost:8088/api/v1/dataset/{d["id"]}', headers=headers)
        print(f'  Status: {r3.status_code}')

# List remaining datasets
r4 = requests.get('http://localhost:8088/api/v1/dataset/?q=(page_size:100)', headers=headers)
data2 = r4.json()
print()
print('Remaining datasets:')
for d in data2.get('result', []):
    print(f'  id={d["id"]} {d["table_name"]} (schema={d.get("schema","")})')
