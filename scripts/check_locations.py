import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("Location Check")

# Check all bronze table locations
for tbl in ["data_referensi_mahasiswa", "data_khs", "data_program_studi", "data_kelas", "data_kurikulum"]:
    try:
        rows = spark.sql(f"DESCRIBE EXTENDED iceberg.bronze.{tbl}").collect()
        for row in rows:
            if hasattr(row, '__iter__') and len(row) >= 2 and row[0] == "Location":
                print(f"BRONZE {tbl}: {row[1]}")
    except Exception as e:
        print(f"BRONZE {tbl} ERROR: {e}")

# Check silver table locations
for tbl in ["silver_khs", "silver_mahasiswa", "silver_program_studi", "silver_kelas", "silver_kurikulum"]:
    try:
        rows = spark.sql(f"DESCRIBE EXTENDED iceberg.silver.{tbl}").collect()
        for row in rows:
            if hasattr(row, '__iter__') and len(row) >= 2 and row[0] == "Location":
                print(f"SILVER {tbl}: {row[1]}")
    except Exception as e:
        print(f"SILVER {tbl} ERROR: {e}")

spark.stop()
