import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
spark = get_spark("Check Gold")
print("=== GOLD TABLES ===")
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").collect():
    tbl = list(r)[1]
    desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.gold.{tbl}").collect()
    loc = [list(row)[1] for row in desc if list(row)[0] == "Location"][0]
    print(f"  {tbl}: {loc}")
spark.stop()
