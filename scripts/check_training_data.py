import sys, os, time
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Check Training Data")
ns = ICEBERG_NAMESPACE

td = spark.table(f"{ns}.feature_store.training_dataset")
print("=== training_dataset schema ===")
td.printSchema()
print(f"Rows: {td.count()}")
td.show(5, truncate=False)

dm = spark.table(f"{ns}.gold.dim_mahasiswa")
print("=== dim_mahasiswa schema ===")
dm.printSchema()
print(f"Rows: {dm.count()}")
dm.show(5, truncate=False)

fk = spark.table(f"{ns}.gold.fact_khs")
print("=== fact_khs schema ===")
fk.printSchema()
print(f"Rows: {fk.count()}")
fk.show(5, truncate=False)

# Try the join that Model B needs
print("\n=== JOIN: dim_mahasiswa + fact_khs ===")
joined = dm.join(fk, "id_mahasiswa", "inner")
print(f"Joined rows: {joined.count()}")
joined_cols = ["id_mahasiswa", "jenis_kelamin", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk"]
try:
    joined.select(*joined_cols).show(5, truncate=False)
except Exception as e:
    print(f"Select error: {e}")
    joined.printSchema()
    joined.show(5, truncate=False)

# Check status_kelulusan in training_dataset
print("\n=== status_kelulusan distribution ===")
td.groupBy("status_kelulusan").count().show()

spark.stop()
