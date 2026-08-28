import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark

spark = get_spark("Clean HMS")

# Remove the phantom table from Hive Metastore directly via JDBC
try:
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW hms_tbls
        USING jdbc
        OPTIONS (
            'url' 'jdbc:postgresql://postgres-hive:5432/metastore',
            'dbtable' 'TBLS'
        )
    """)
    stuck = spark.sql("SELECT TBL_ID, TBL_NAME FROM hms_tbls WHERE TBL_NAME = 'gold_mahasiswa_lama'").collect()
    print(f"Found in HMS: {stuck}")
except Exception as e:
    print(f"HMS query error: {e}")

spark.stop()
