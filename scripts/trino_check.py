import requests
import time

# First query
r = requests.post(
    'http://trino:8082/v1/statement',
    headers={'X-Trino-User': 'admin', 'Content-Type': 'text/plain'},
    data='SHOW TABLES FROM iceberg.gold',
    timeout=30
)
result = r.json()

# Follow nextUri until we get results
for i in range(10):
    next_uri = result.get('nextUri')
    if not next_uri:
        break
    time.sleep(1)
    r = requests.get(next_uri, headers={'X-Trino-User': 'admin'}, timeout=30)
    result = r.json()
    data = result.get('data', [])
    print(f'Attempt {i+1}: {len(data)} rows')

print('Final data:', result.get('data', []))
print('Error:', result.get('error'))

# Now query dim_mahasiswa_fix
print('\n--- Query dim_mahasiswa_fix ---')
r = requests.post(
    'http://trino:8082/v1/statement',
    headers={'X-Trino-User': 'admin', 'Content-Type': 'text/plain'},
    data='SELECT count(*) FROM iceberg.gold.dim_mahasiswa_fix',
    timeout=30
)
result = r.json()
for i in range(10):
    next_uri = result.get('nextUri')
    if not next_uri:
        break
    time.sleep(1)
    r = requests.get(next_uri, headers={'X-Trino-User': 'admin'}, timeout=30)
    result = r.json()
print('dim_mahasiswa_fix count:', result.get('data', []))
print('Error:', result.get('error'))
