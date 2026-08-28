import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Verify Silver")

print("=== ALL TABLES WITH LOCATIONS ===")
for ns in ["bronze", "silver", "gold", "feature_store"]:
    try:
        for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.{ns}").collect():
            tbl = list(r)[1]
            desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.{ns}.{tbl}").collect()
            loc = [list(row)[1] for row in desc if list(row)[0] == "Location"][0]
            cnt = spark.sql(f"SELECT count(*) as c FROM {ICEBERG_NAMESPACE}.{ns}.{tbl}").collect()[0].c
            status = "OK" if loc.startswith("s3a:") else "WRONG"
            print(f"  {ns}.{tbl}: {cnt} rows [{status}]")
    except Exception:
        pass

spark.stop()
