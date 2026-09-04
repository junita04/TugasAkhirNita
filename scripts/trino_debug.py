import requests
import time
import json

def run_trino_full(sql):
    r = requests.post('http://trino:8082/v1/statement', 
                      headers={'X-Trino-User': 'admin', 'Content-Type': 'text/plain'}, 
                      data=sql)
    result = r.json()
    print(f'  Initial: state={result.get("stats", {}).get("state")} next={bool(result.get("nextUri"))}')
    
    for i in range(20):
        uri = result.get('nextUri')
        if not uri:
            break
        time.sleep(2)
        r = requests.get(uri, headers={'X-Trino-User': 'admin'})
        result = r.json()
        state = result.get('stats', {}).get('state', 'unknown')
        has_next = bool(result.get('nextUri'))
        data_len = len(result.get('data', []) or [])
        print(f'  Iter {i}: state={state} next={has_next} data={data_len}')
    
    return result

# Show catalogs
print('=== SHOW CATALOGS ===')
r = run_trino_full('SHOW CATALOGS')
data = r.get('data')
if data:
    for row in data:
        print(f'  {row}')
else:
    print('  No data')
    print('  Full keys:', list(r.keys()))
    if r.get('error'):
        print('  Error:', r['error'].get('message', '')[:200])
