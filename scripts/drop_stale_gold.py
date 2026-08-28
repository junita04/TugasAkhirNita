import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Drop Stale Gold Tables")

# Drop ALL gold tables with wrong file:/// locations
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect():
    tbl = list(r)[1]
    try:
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.{tbl}")
        print(f"DROPPED gold.{tbl}")
    except Exception as e:
        print(f"Error dropping gold.{tbl}: {e}")

# Verify
tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect()
print(f"\nRemaining gold tables: {len(tables)}")
for r in tables:
    print(f"  {list(r)[1]}")

spark.stop()
print("\nDONE")
