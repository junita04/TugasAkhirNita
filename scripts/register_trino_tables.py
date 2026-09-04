"""
Register Iceberg _fix tables with Trino using CALL system.register_table
"""
import requests

TRINO_URL = "http://trino:8082"

tables_to_register = [
    ("gold", "dim_mahasiswa_fix"),
    ("gold", "fact_khs_fix"),
]

for schema, table_name in tables_to_register:
    print(f"\n--- {schema}.{table_name} ---")
    
    # First try to unregister (ignore error if not exists)
    unreg_sql = f"CALL iceberg.system.unregister_table('{schema}', '{table_name}')"
    try:
        r = requests.post(
            f"{TRINO_URL}/v1/statement",
            headers={"X-Trino-User": "admin", "Content-Type": "text/plain"},
            data=unreg_sql,
            timeout=30
        )
        print(f"  Unregister: {r.status_code}")
    except Exception as e:
        print(f"  Unregister error (ok): {e}")
    
    # Get the metadata location from MinIO
    # The Iceberg table metadata is at: s3a://warehouse/iceberg/{schema}/{table_name}/metadata/v1.metadata.json
    # We need to find the correct metadata file location
    
    # Register using the metadata JSON location
    # For Iceberg tables created by Spark, the metadata is at:
    # s3a://warehouse/iceberg/{schema}/{table_name}/metadata/v1.metadata.json
    metadata_location = f"s3a://warehouse/iceberg/{schema}/{table_name}/metadata/v1.metadata.json"
    
    reg_sql = f"CALL iceberg.system.register_table('{schema}', '{table_name}', '{metadata_location}')"
    try:
        r = requests.post(
            f"{TRINO_URL}/v1/statement",
            headers={"X-Trino-User": "admin", "Content-Type": "text/plain"},
            data=reg_sql,
            timeout=30
        )
        if r.status_code == 200:
            result = r.json()
            if result.get("error"):
                print(f"  Register error: {result['error'].get('message', 'unknown')}")
            else:
                print(f"  Register: OK")
        else:
            print(f"  Register HTTP error: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  Register error: {e}")

# Verify by querying the tables
print("\n--- Verify tables in Trino ---")
for schema, table_name in tables_to_register:
    try:
        r = requests.post(
            f"{TRINO_URL}/v1/statement",
            headers={"X-Trino-User": "admin", "Content-Type": "text/plain"},
            data=f"SELECT count(*) FROM iceberg.{schema}.{table_name}",
            timeout=30
        )
        if r.status_code == 200:
            result = r.json()
            if result.get("error"):
                print(f"  {schema}.{table_name}: ERROR - {result['error'].get('message', 'unknown')}")
            else:
                cols = result.get("columns", [])
                data = result.get("data", [])
                if data:
                    print(f"  {schema}.{table_name}: {data[0][0]} rows")
                else:
                    print(f"  {schema}.{table_name}: query returned no data")
        else:
            print(f"  {schema}.{table_name}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  {schema}.{table_name}: ERROR {e}")

print("\nDONE.")
