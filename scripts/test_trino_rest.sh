#!/bin/bash
# Test Trino REST API with plain-text SQL body - full polling
RESP=$(curl -s -X POST http://trino:8082/v1/statement \
  -H 'X-Trino-User: airflow' \
  -H 'X-Trino-Catalog: iceberg' \
  -H 'X-Trino-Schema: gold' \
  --data-binary 'SELECT 1 AS val')
NEXT_URI=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('nextUri',''))")
echo "NEXT_URI=$NEXT_URI"
while [ -n "$NEXT_URI" ]; do
  sleep 1
  R=$(curl -s -H 'X-Trino-User: airflow' "$NEXT_URI")
  echo "$R" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'data' in d:
    print('DATA:', d['data'])
    print('COLUMNS:', d.get('columns'))
elif 'error' in d:
    print('ERROR:', d['error']['message'][:300])
else:
    print('STATE:', d.get('stats',{}).get('state'))
"
  NEXT_URI=$(echo "$R" | python3 -c "import sys,json; print(json.load(sys.stdin).get('nextUri',''))")
done
echo "DONE"
