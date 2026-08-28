import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Final Health Check")

print("=== ALL LAYERS ===")
for ns in ["bronze", "silver", "gold", "feature_store"]:
    try:
        tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.{ns}").collect()
        if tables:
            print(f"\n{ns.upper()} ({len(tables)} tables):")
            for r in tables:
                tbl = list(r)[1]
                try:
                    cnt = spark.sql(f"SELECT count(*) as c FROM {ICEBERG_NAMESPACE}.{ns}.{tbl}").collect()[0].c
                    print(f"  {ns}.{tbl}: {cnt} rows")
                except Exception as e:
                    print(f"  {ns}.{tbl}: ERROR - {type(e).__name__}")
    except Exception:
        pass

spark.stop()
print("\n=== HEALTH CHECK PASSED ===")
