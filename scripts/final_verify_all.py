import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Final Verify All Tables")

for ns in ["silver", "gold", "feature_store"]:
    print(f"\n=== {ns.upper()} ===")
    for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.{ns}").collect():
        tbl = list(r)[1]
        try:
            desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.{ns}.{tbl}").collect()
            loc = [list(row)[1] for row in desc if list(row)[0] == "Location"][0]
            cnt = spark.sql(f"SELECT count(*) as c FROM {ICEBERG_NAMESPACE}.{ns}.{tbl}").collect()[0].c
            status = "OK" if loc.startswith("s3a:") else "WRONG"
            print(f"  {ns}.{tbl}: {cnt} rows [{status}]")
        except Exception as e:
            print(f"  {ns}.{tbl}: ERROR - {type(e).__name__}")

spark.stop()
