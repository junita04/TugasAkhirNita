import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Force Drop Gold v2")

tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect()
print(f"Remaining tables: {len(tables)}")
for r in tables:
    tbl = list(r)[1]
    print(f"  Table: {tbl}")
    try:
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.{tbl} PURGE")
        print(f"  -> PURGED")
    except Exception as e:
        print(f"  -> Error: {e}")

# Check again
tables2 = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect()
print(f"\nFinal count: {len(tables2)}")
for r in tables2:
    print(f"  {list(r)[1]}")

spark.stop()
