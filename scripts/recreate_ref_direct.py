"""
Re-create data_referensi_mahasiswa in Bronze from Excel.
Directly uses Spark to read the sheet and write to Iceberg.
"""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark

spark = get_spark("Recreate Bronze data_referensi_mahasiswa")

file_path = "/opt/airflow/data/(asli)req_data_rut (1).xlsx"
sheet = "Referensi Data Mahasiswa"

df = (
    spark.read
    .format("com.crealytics.spark.excel")
    .option("header", "true")
    .option("inferSchema", "true")
    .option("dataAddress", f"'{sheet}'!A1")
    .load(file_path)
)

df = df.coalesce(1)
row_count = df.count()
print(f"Rows read: {row_count}")
print(f"Columns: {df.columns}")

spark.sql("DROP TABLE IF EXISTS iceberg.bronze.data_referensi_mahasiswa")

(
    df.write
    .format("iceberg")
    .mode("overwrite")
    .saveAsTable("iceberg.bronze.data_referensi_mahasiswa")
)

# Verify
desc = spark.sql("DESCRIBE EXTENDED iceberg.bronze.data_referensi_mahasiswa").collect()
for row in desc:
    if list(row)[0] == "Location":
        print(f"Location: {list(row)[1]}")

cnt = spark.sql("SELECT count(*) as c FROM iceberg.bronze.data_referensi_mahasiswa").collect()[0].c
print(f"Verified count: {cnt}")

spark.stop()
print("DONE")
