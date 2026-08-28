import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
spark = get_spark("Bronze Verify")
tables = ['data_referensi_mahasiswa','data_program_studi','data_kelas','data_kurikulum','data_khs']
for t in tables:
    try:
        cnt = spark.sql(f"SELECT count(*) as c FROM iceberg.bronze.{t}").collect()[0].c
        print(f"{t}: {cnt} rows")
    except Exception as e:
        print(f"{t}: ERROR - {e}")
spark.stop()
