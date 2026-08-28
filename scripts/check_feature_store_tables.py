import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Check Feature Store")

print("=== FEATURE_STORE TABLES ===")
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.feature_store").collect():
    tbl = list(r)[1]
    try:
        desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.feature_store.{tbl}").collect()
        loc = [list(row)[1] for row in desc if list(row)[0] == "Location"][0]
        cnt = spark.sql(f"SELECT count(*) as c FROM {ICEBERG_NAMESPACE}.feature_store.{tbl}").collect()[0].c
        status = "OK" if loc.startswith("s3a:") else "WRONG"
        print(f"  feature_store.{tbl}: {cnt} rows [{status}] - {loc}")
    except Exception as e:
        print(f"  feature_store.{tbl}: ERROR - {e}")

spark.stop()
