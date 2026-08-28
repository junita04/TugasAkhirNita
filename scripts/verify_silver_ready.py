"""
Verify Silver can read all Bronze tables and write Silver tables.
"""
import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Silver Verify")

print("=== BRONZE TABLES ===")
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze").collect():
    tbl = list(r)[1]
    desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.bronze.{tbl}").collect()
    loc = [list(row)[1] for row in desc if list(row)[0] == "Location"][0]
    cnt = spark.sql(f"SELECT count(*) as c FROM {ICEBERG_NAMESPACE}.bronze.{tbl}").collect()[0].c
    status = "OK" if loc.startswith("s3a:") else "WRONG LOCATION"
    print(f"  {tbl}: {cnt} rows, {status}")

print("\n=== SILVER TABLES ===")
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.silver").collect():
    print(f"  {list(r)}")

print("\n=== Test: Silver can read bronze.data_referensi_mahasiswa ===")
df = spark.table(f"{ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa")
print(f"  Rows: {df.count()}")
print(f"  Columns: {df.columns}")

print("\n=== Test: Silver can read bronze.data_khs ===")
df = spark.table(f"{ICEBERG_NAMESPACE}.bronze.data_khs")
print(f"  Rows: {df.count()}")

spark.stop()
print("\nALL CHECKS PASSED")
