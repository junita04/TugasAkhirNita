import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Drop Stale Feature Store")

for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.feature_store").collect():
    tbl = list(r)[1]
    try:
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.feature_store.{tbl} PURGE")
        print(f"DROPPED feature_store.{tbl}")
    except Exception as e:
        print(f"Error dropping feature_store.{tbl}: {e}")

tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.feature_store").collect()
print(f"\nRemaining feature_store tables: {len(tables)}")
spark.stop()
