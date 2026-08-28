import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("File NS Check")

# Check what's under the file: namespace
try:
    for r in spark.sql("SHOW TABLES IN iceberg.`file:`").collect():
        print("FILE_NS:", list(r))
except Exception as e:
    print(f"file: namespace tables error: {e}")

# Check table locations for silver tables
for tbl in ["silver_khs", "silver_mahasiswa"]:
    try:
        loc = spark.sql(f"DESCRIBE EXTENDED iceberg.silver.{tbl}").collect()
        for row in loc:
            if "Location" in str(row) or "location" in str(row):
                print(f"  {tbl} location: {row}")
    except Exception as e:
        print(f"  {tbl} desc error: {e}")

# Check where data_referensi_mahasiswa is in bronze
try:
    loc = spark.sql("DESCRIBE EXTENDED iceberg.bronze.data_referensi_mahasiswa").collect()
    for row in loc:
        if "Location" in str(row) or "location" in str(row):
            print(f"  bronze.data_referensi_mahasiswa: {row}")
except Exception as e:
    print(f"  bronze ref desc error: {e}")

spark.stop()
