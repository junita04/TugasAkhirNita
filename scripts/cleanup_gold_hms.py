import sys, os
sys.path.insert(0, "/opt/airflow")

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("Cleanup Gold")
    .master("spark://spark-master:7077")
    .config("spark.jars", "/opt/airflow/jars/*")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hadoop")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.hadoop.HadoopFileIO")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.driver.memory", "1g")
    .config("spark.executor.instances", "2")
    .config("spark.executor.memory", "512m")
    .config("spark.executor.cores", "1")
    .config("spark.dynamicAllocation.enabled", "false")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)

# Try to use HMS catalog to clean up
try:
    # Drop via Spark with catalog override
    spark.sql("DROP TABLE IF EXISTS iceberg.gold.gold_mahasiswa_lama PURGE")
    print("Dropped via iceberg catalog")
except Exception as e:
    print(f"Error with PURGE: {e}")

# List remaining
tables = spark.sql("SHOW TABLES IN iceberg.gold").collect()
print(f"Remaining: {len(tables)}")
for r in tables:
    print(f"  {list(r)[1]}")

# If still stuck, delete from HMS database directly via JDBC
if len(tables) > 0:
    print("\nTrying HMS JDBC cleanup...")
    try:
        # Connect to HMS Postgres
        spark.sql("""
            CREATE OR REPLACE TEMPORARY VIEW hms_tbls
            USING jdbc
            OPTIONS (
                'url' 'jdbc:postgresql://postgres-hive:5432/metastore',
                'dbtable' 'TBLS'
            )
        """)
        # Find and show the stuck table
        stuck = spark.sql("SELECT TBL_ID, TBL_NAME, TBL_TYPE FROM hms_tbls WHERE TBL_NAME LIKE '%gold_mahasiswa_lama%'").collect()
        print(f"Found in HMS: {stuck}")
    except Exception as e:
        print(f"HMS cleanup error: {e}")

spark.stop()
