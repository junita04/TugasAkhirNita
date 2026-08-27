"""Check KHS data availability for ip and sks_seharusnya"""
import warnings
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

spark = (
    SparkSession.builder
    .appName("TA_Check_KHS")
    .master("local[*]")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3.path.style.access", "true")
    .config("spark.hadoop.fs.s3.connection.ssl.enabled", "false")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hive")
    .config("spark.sql.catalog.iceberg.uri", "thrift://hive-metastore:9083")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# Check all tables in bronze
print("=" * 70)
print("ALL BRONZE TABLES")
print("=" * 70)
for t in spark.sql("SHOW TABLES IN iceberg.bronze").collect():
    print(f"  {t[1]}")

print("\nALL SILVER TABLES")
for t in spark.sql("SHOW TABLES IN iceberg.silver").collect():
    print(f"  {t[1]}")

print("\nALL GOLD TABLES")
for t in spark.sql("SHOW TABLES IN iceberg.gold").collect():
    print(f"  {t[1]}")

# Check if KHS data exists in Bronze
print("\n" + "=" * 70)
print("CHECK BRONZE KHS")
print("=" * 70)
try:
    df_khs = spark.table("iceberg.bronze.data_khs")
    print(f"data_khs rows: {df_khs.count()}")
    print(f"columns: {df_khs.columns}")
    df_khs.printSchema()
    df_khs.show(5, truncate=False)
except Exception as e:
    print(f"NOT FOUND: {e}")

# Check Gold for ip
print("\n" + "=" * 70)
print("CHECK GOLD COLUMNS")
print("=" * 70)
df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")
print(f"Gold columns: {df_gold.columns}")

# Check if ip exists
has_ip = "ip" in df_gold.columns
has_sks_seharusnya = "sks_seharusnya" in df_gold.columns
has_target_sks = "target_sks_kumulatif" in df_gold.columns
print(f"Has 'ip': {has_ip}")
print(f"Has 'sks_seharusnya': {has_sks_seharusnya}")
print(f"Has 'target_sks_kumulatif': {has_target_sks}")

# Check KHS from Excel
print("\n" + "=" * 70)
print("CHECK KHS FROM EXCEL")
print("=" * 70)
import pandas as pd
try:
    df_khs_excel = pd.read_excel("/tmp/(asli)req_data_rut (baru).xlsx", sheet_name="Data KHS", dtype=str)
    df_khs_excel.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_khs_excel.columns]
    print(f"KHS Excel rows: {len(df_khs_excel)}")
    print(f"KHS Excel columns: {list(df_khs_excel.columns)}")
    
    # Check for target IDs in KHS
    print("\nTarget IDs in KHS:")
    for mid in TARGET_IDS:
        rows = df_khs_excel[df_khs_excel["id_mhs"] == mid]
        if len(rows) > 0:
            print(f"  {mid}: {len(rows)} records")
            for _, r in rows.head(3).iterrows():
                print(f"    {dict(r)}")
        else:
            print(f"  {mid}: NOT in KHS")
    
    # Check ip column
    if "ip" in df_khs_excel.columns:
        print(f"\nip values in KHS:")
        print(df_khs_excel["ip"].describe())
    
    # Check sks column
    if "sks" in df_khs_excel.columns:
        print(f"\nsks values in KHS:")
        print(df_khs_excel["sks"].describe())
        
except Exception as e:
    print(f"Error: {e}")

spark.stop()
