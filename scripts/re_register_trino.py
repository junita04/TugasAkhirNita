import requests

TRINO_URL = "http://trino:8082"

tables = [
    ("gold", "dim_mahasiswa_fix", "v1.metadata.json"),
    ("gold", "fact_khs_fix", "v2.metadata.json"),
]

for schema, table_name, meta_file in tables:
    print(f"\n--- {schema}.{table_name} ---")
    
    # Unregister first
    unreg = f"CALL iceberg.system.unregister_table('{schema}', '{table_name}')"
    r = requests.post(f"{TRINO_URL}/v1/statement", headers={"X-Trino-User": "admin", "Content-Type": "text/plain"}, data=unreg, timeout=30)
    print(f"  Unregister: {r.status_code}")
    
    # Register with correct metadata file
    metadata = f"s3a://warehouse/iceberg/{schema}/{table_name}/metadata/{meta_file}"
    reg = f"CALL iceberg.system.register_table('{schema}', '{table_name}', '{metadata}')"
    r = requests.post(f"{TRINO_URL}/v1/statement", headers={"X-Trino-User": "admin", "Content-Type": "text/plain"}, data=reg, timeout=30)
    
    import time
    result = r.json()
    for i in range(5):
        next_uri = result.get("nextUri")
        if not next_uri:
            break
        time.sleep(1)
        r = requests.get(next_uri, headers={"X-Trino-User": "admin"}, timeout=30)
        result = r.json()
    
    if result.get("error"):
        print(f"  Register ERROR: {result['error'].get('message', 'unknown')[:100]}")
    else:
        print(f"  Register: OK")

# Verify
print("\n--- Verify in Trino ---")
for schema, table_name, _ in tables:
    r = requests.post(f"{TRINO_URL}/v1/statement", headers={"X-Trino-User": "admin", "Content-Type": "text/plain"}, 
                      data=f"SELECT count(*) FROM iceberg.{schema}.{table_name}", timeout=30)
    result = r.json()
    for i in range(5):
        next_uri = result.get("nextUri")
        if not next_uri:
            break
        time.sleep(1)
        r = requests.get(next_uri, headers={"X-Trino-User": "admin"}, timeout=30)
        result = r.json()
    
    if result.get("error"):
        print(f"  {schema}.{table_name}: ERROR - {result['error'].get('message', 'unknown')[:80]}")
    else:
        data = result.get("data", [])
        print(f"  {schema}.{table_name}: {data[0][0] if data else 'no data'} rows")

# Show all gold tables
print("\n--- SHOW TABLES FROM iceberg.gold ---")
r = requests.post(f"{TRINO_URL}/v1/statement", headers={"X-Trino-User": "admin", "Content-Type": "text/plain"}, 
                  data="SHOW TABLES FROM iceberg.gold", timeout=30)
result = r.json()
for i in range(10):
    next_uri = result.get("nextUri")
    if not next_uri:
        break
    time.sleep(1)
    r = requests.get(next_uri, headers={"X-Trino-User": "admin"}, timeout=30)
    result = r.json()

for row in result.get("data", []):
    print(f"  {row}")
