import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Force Drop Stale Gold")

# Try force drop remaining tables
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect():
    tbl = list(r)[1]
    try:
        # Try with PURGE to clean up metadata
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.{tbl} PURGE")
        print(f"PURGED gold.{tbl}")
    except Exception as e:
        print(f"Error purging gold.{tbl}: {e}")
        try:
            # Fallback: try basic DROP
            spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.{tbl}")
            print(f"DROPPED gold.{tbl}")
        except Exception as e2:
            print(f"Error dropping gold.{tbl}: {e2}")

# Verify
tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect()
print(f"\nRemaining gold tables: {len(tables)}")

spark.stop()
print("\nDONE")
