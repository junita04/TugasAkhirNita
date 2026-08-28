#!/bin/bash
# Check Superset via curl
TOKEN=$(curl -s -X POST http://superset:8088/api/v1/security/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change-me"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "=== Dashboard ==="
curl -s http://superset:8088/api/v1/dashboard/3 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('result',{})
print(f\"Title: {d.get('dashboard_title','N/A')}\")"

echo ""
echo "=== Gold Datasets ==="
curl -s "http://superset:8088/api/v1/dataset/?q=(page_size:50)" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
for d in json.load(sys.stdin).get('result',[]):
    if 'gold' in d.get('schema',''):
        print(f\"  id={d['id']} {d['schema']}.{d['table_name']}\")"

echo ""
echo "=== Charts ==="
curl -s "http://superset:8088/api/v1/chart/?q=(page_size:100)" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
for c in json.load(sys.stdin).get('result',[]):
    print(f\"  id={c['id']} {c['slice_name']}\")"
