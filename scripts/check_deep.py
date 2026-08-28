import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("Deep Check")

# Check all namespaces
print("=== ALL NAMESPACES ===")
for r in spark.sql("SHOW NAMESPACES IN iceberg").collect():
    ns = list(r)[0]
    print(f"  namespace: {ns}")
    try:
        tables = spark.sql(f"SHOW TABLES IN iceberg.`{ns}`").collect()
        for t in tables:
            print(f"    table: {list(t)}")
    except:
        pass

# Try to describe data_referensi_mahasiswa in different ways
print("\n=== LOOKING FOR data_referensi_mahasiswa ===")
# List ALL tables across ALL namespaces
for r in spark.sql("SHOW TABLES IN iceberg").collect():
    row = list(r)
    if len(row) >= 2 and "referensi" in str(row[1]).lower():
        print(f"  FOUND: {row}")

# Check the local namespace
print("\n=== LOCAL NAMESPACE ===")
try:
    for r in spark.sql("SHOW TABLES IN iceberg.`local`").collect():
        print(f"  local table: {list(r)}")
except Exception as e:
    print(f"  local ns error: {e}")

spark.stop()
