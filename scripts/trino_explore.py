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

# Show all schemas
print("=== SHOW SCHEMAS ===")
r = run_trino("SHOW SCHEMAS FROM iceberg")
for row in r.get("data", []):
    print(f"  {row}")

# Show all tables in gold
print("\n=== SHOW TABLES FROM iceberg.gold ===")
r = run_trino("SHOW TABLES FROM iceberg.gold")
for row in r.get("data", []):
    print(f"  {row}")

# Check what Hive Metastore has
print("\n=== SHOW SCHEMAS FROM hive ===")
r = run_trino("SHOW SCHEMAS FROM hive")
for row in r.get("data", []):
    print(f"  {row}")

# Show tables in hive.gold
print("\n=== SHOW TABLES FROM hive.gold ===")
r = run_trino("SHOW TABLES FROM hive.gold")
for row in r.get("data", []):
    print(f"  {row}")

# Try accessing via hive catalog
print("\n=== SELECT count(*) FROM hive.gold.dim_mahasiswa_fix ===")
r = run_trino("SELECT count(*) FROM hive.gold.dim_mahasiswa_fix")
if r.get("error"):
    print(f"  ERROR: {r['error'].get('message', 'unknown')[:100]}")
else:
    print(f"  Data: {r.get('data', [])}")

print("\n=== SELECT count(*) FROM hive.gold.fact_khs_fix ===")
r = run_trino("SELECT count(*) FROM hive.gold.fact_khs_fix")
if r.get("error"):
    print(f"  ERROR: {r['error'].get('message', 'unknown')[:100]}")
else:
    print(f"  Data: {r.get('data', [])}")
