import requests
import time

TRINO_URL = "http://trino:8082"

def run_trino(sql):
    r = requests.post(f"{TRINO_URL}/v1/statement", headers={"X-Trino-User": "admin", "Content-Type": "text/plain"}, data=sql, timeout=60)
    result = r.json()
    for i in range(20):
        next_uri = result.get("nextUri")
        if not next_uri:
            break
        time.sleep(1)
        r = requests.get(next_uri, headers={"X-Trino-User": "admin"}, timeout=60)
        result = r.json()
    return result

# Check all catalogs
print("=== SHOW CATALOGS ===")
r = run_trino("SHOW CATALOGS")
for row in r.get("data", []):
    print(f"  {row}")

# Check all schemas in iceberg catalog
print("\n=== SHOW SCHEMAS IN iceberg ===")
r = run_trino("SHOW SCHEMAS IN iceberg")
for row in r.get("data", []):
    print(f"  {row}")

# List all tables in gold schema
print("\n=== SHOW TABLES IN iceberg.gold ===")
r = run_trino("SHOW TABLES IN iceberg.gold")
for row in r.get("data", []):
    print(f"  {row}")
