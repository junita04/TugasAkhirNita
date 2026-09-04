import requests
import time

def run_trino(sql):
    r = requests.post('http://trino:8082/v1/statement', 
                      headers={'X-Trino-User': 'admin', 'Content-Type': 'text/plain'}, 
                      data=sql)
    result = r.json()
    for i in range(20):
        uri = result.get('nextUri')
        if not uri:
            break
        time.sleep(2)
        r = requests.get(uri, headers={'X-Trino-User': 'admin'})
        result = r.json()
    return result

# Show catalogs
print('=== SHOW CATALOGS ===')
r = run_trino('SHOW CATALOGS')
print('Data:', r.get('data'))
print('Error:', r.get('error'))

# Show schemas in iceberg
print('\n=== SHOW SCHEMAS IN iceberg ===')
r = run_trino('SHOW SCHEMAS IN iceberg')
print('Data:', r.get('data'))
print('Error:', r.get('error'))

# Show tables in iceberg.gold
print('\n=== SHOW TABLES IN iceberg.gold ===')
r = run_trino('SHOW TABLES IN iceberg.gold')
print('Data:', r.get('data'))
print('Error:', r.get('error'))
