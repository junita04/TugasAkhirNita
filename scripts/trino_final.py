import requests
import time

def run_trino(sql):
    r = requests.post('http://trino:8082/v1/statement', 
                      headers={'X-Trino-User': 'admin', 'Content-Type': 'text/plain'}, 
                      data=sql)
    result = r.json()
    all_data = []
    
    for i in range(20):
        data = result.get('data')
        if data:
            all_data.extend(data)
        
        uri = result.get('nextUri')
        if not uri:
            break
        time.sleep(2)
        r = requests.get(uri, headers={'X-Trino-User': 'admin'})
        result = r.json()
    
    return all_data

# Show catalogs
print('=== SHOW CATALOGS ===')
data = run_trino('SHOW CATALOGS')
for row in data:
    print(f'  {row}')

# Show schemas in iceberg
print('\n=== SHOW SCHEMAS IN iceberg ===')
data = run_trino('SHOW SCHEMAS IN iceberg')
for row in data:
    print(f'  {row}')

# Show tables in iceberg.gold
print('\n=== SHOW TABLES IN iceberg.gold ===')
data = run_trino('SHOW TABLES IN iceberg.gold')
for row in data:
    print(f'  {row}')

# Count dim_mahasiswa_fix
print('\n=== COUNT dim_mahasiswa_fix ===')
data = run_trino('SELECT count(*) FROM iceberg.gold.dim_mahasiswa_fix')
print(f'  {data}')

# Count fact_khs_fix
print('\n=== COUNT fact_khs_fix ===')
data = run_trino('SELECT count(*) FROM iceberg.gold.fact_khs_fix')
print(f'  {data}')
