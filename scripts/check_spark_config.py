import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("Config Check")

# Check all iceberg catalog configs
for key in ["spark.sql.catalog.iceberg.warehouse",
            "spark.sql.catalog.iceberg.type",
            "spark.sql.catalog.iceberg.cache-enabled",
            "spark.sql.catalog.local.warehouse",
            "spark.sql.catalog.local.type"]:
    try:
        val = spark.conf.get(key)
        print(f"{key} = {val}")
    except Exception:
        print(f"{key} = (not set)")

# Check where tables exist
try:
    result = spark.sql("SHOW NAMESPACES IN iceberg").collect()
    print(f"Namespaces in iceberg: {[r.namespaceName for r in result]}")
except Exception as e:
    print(f"SHOW NAMESPACES error: {e}")

spark.stop()
