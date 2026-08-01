from backend.spark.session import get_spark

spark = get_spark()

print("=" * 60)
print("TABLE GOLD")
print("=" * 60)

spark.sql("SHOW TABLES IN local.gold").show(truncate=False)

print("=" * 60)
print("SAMPLE DATA")
print("=" * 60)

spark.table("local.gold.gold_mahasiswa").show(5, truncate=False)

# python -m scripts.check_gold