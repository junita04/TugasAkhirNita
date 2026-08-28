"""Check what tables Spark can see."""
import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("check")

print("\n=== SHOW DATABASES ===")
spark.sql("SHOW DATABASES").show(50, truncate=False)

print("\n=== SHOW TABLES IN iceberg.feature_store ===")
try:
    spark.sql("SHOW TABLES IN iceberg.feature_store").show(50, truncate=False)
except Exception as e:
    print(f"Error: {e}")

print("\n=== SHOW TABLES IN iceberg.gold ===")
try:
    spark.sql("SHOW TABLES IN iceberg.gold").show(50, truncate=False)
except Exception as e:
    print(f"Error: {e}")

# Try listing all tables in all schemas
for schema in ["bronze", "silver", "gold", "feature_store"]:
    print(f"\n=== SHOW TABLES IN iceberg.{schema} ===")
    try:
        spark.sql(f"SHOW TABLES IN iceberg.{schema}").show(50, truncate=False)
    except Exception as e:
        print(f"Error: {e}")

# Try reading the training_kelulusan directly
print("\n=== Try reading feature_store.training_kelulusan ===")
try:
    df = spark.table("iceberg.feature_store.training_kelulusan")
    print(f"Rows: {df.count()}")
    df.printSchema()
except Exception as e:
    print(f"Error: {e}")

# Check if the table exists in a different namespace
print("\n=== Try reading local.feature_store.training_kelulusan ===")
try:
    df = spark.table("local.feature_store.training_kelulusan")
    print(f"Rows: {df.count()}")
except Exception as e:
    print(f"Error: {e}")
