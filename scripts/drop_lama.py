import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Drop Lame Tables")

# Drop all _lama tables in bronze
for r in spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze").collect():
    tbl = list(r)[1]
    if "_lama" in tbl:
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.bronze.{tbl}")
        print(f"DROPPED bronze.{tbl}")

spark.stop()
print("DONE")
