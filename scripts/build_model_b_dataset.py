import sys, os, time
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Build Model B Dataset")
ns = ICEBERG_NAMESPACE

td = spark.table(f"{ns}.feature_store.training_dataset")
dm = spark.table(f"{ns}.gold.dim_mahasiswa")

# Join and build 8-feature dataset
# training_dataset has: id_mahasiswa, ip, sks, angkatan, jumlah_mk, status_kelulusan
# dim_mahasiswa has: id_mahasiswa, jenis_kelamin, ipk, total_sks, jumlah_mk, ...
# We need from dim_mahasiswa: jenis_kelamin, ipk, total_sks
td.createOrReplaceTempView("td")
dm.createOrReplaceTempView("dm")

result = spark.sql("""
    SELECT
        td.id_mahasiswa,
        CASE WHEN dm.jenis_kelamin = 'P' THEN 0 ELSE 1 END AS jk_enc,
        td.angkatan,
        td.ip,
        dm.ipk,
        dm.total_sks,
        td.jumlah_mk,
        td.jumlah_mk * 24 AS sks_seharusnya,
        dm.total_sks - (td.jumlah_mk * 24) AS selisih_sks,
        td.status_kelulusan
    FROM td
    INNER JOIN dm ON td.id_mahasiswa = dm.id_mahasiswa
""")

print(f"Final rows: {result.count()}")
print("Final schema:")
result.printSchema()
result.show(10, truncate=False)

# NULL check
print("\n=== NULL check ===")
for col_name in result.columns:
    null_count = result.filter(result[col_name].isNull()).count()
    print(f"  {col_name}: {null_count} NULLs")

# Target distribution
print("\n=== Target distribution ===")
result.groupBy("status_kelulusan").count().show()

# Duplicate check
total = result.count()
distinct = result.select("id_mahasiswa").distinct().count()
print(f"Total rows: {total}, Distinct IDs: {distinct}")
if total != distinct:
    dupes = result.groupBy("id_mahasiswa").count().filter("count > 1").count()
    print(f"WARNING: {dupes} duplicate IDs found!")

# Convert to pandas for ML
print("\n=== Converting to pandas ===")
pdf = result.toPandas()
print(f"Pandas shape: {pdf.shape}")
print(f"Columns: {list(pdf.columns)}")
print(pdf.head())

# Save to CSV for reference
pdf.to_csv("/tmp/model_b_raw_dataset.csv", index=False)
print("Saved raw dataset to /tmp/model_b_raw_dataset.csv")

spark.stop()
