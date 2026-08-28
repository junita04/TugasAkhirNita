"""Check Spark-visible tables."""
import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("check")

# Check training_dataset
print("=== training_dataset schema ===")
df = spark.table("iceberg.feature_store.training_dataset")
df.printSchema()
print(f"Rows: {df.count()}")
df.show(3, truncate=False)

# Check inference_dataset
print("\n=== inference_dataset schema ===")
df2 = spark.table("iceberg.feature_store.inference_dataset")
df2.printSchema()
print(f"Rows: {df2.count()}")
df2.show(3, truncate=False)

# Check dim_mahasiswa
print("\n=== dim_mahasiswa schema ===")
df3 = spark.table("iceberg.gold.dim_mahasiswa")
df3.printSchema()
print(f"Rows: {df3.count()}")
df3.show(3, truncate=False)

# Check fact_khs
print("\n=== fact_khs schema ===")
df4 = spark.table("iceberg.gold.fact_khs")
df4.printSchema()
print(f"Rows: {df4.count()}")
df4.show(3, truncate=False)
