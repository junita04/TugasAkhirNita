from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark()

print("=" * 60)
print("TABLE GOLD")
print("=" * 60)

spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.gold").show(truncate=False)

print("=" * 60)
print("SAMPLE DATA")
print("=" * 60)

spark.table(f"{ICEBERG_NAMESPACE}.gold.gold_mahasiswa").show(5, truncate=False)

# python -m scripts.check_gold