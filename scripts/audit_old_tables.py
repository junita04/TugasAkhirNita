"""Check for old/duplicate tables in Iceberg catalog"""
import warnings
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = (
    SparkSession.builder
    .appName("TA_Audit_Old_Tables")
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

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

# ============================================================
# 1. LIST ALL TABLES IN ALL NAMESPACES
# ============================================================
print("=" * 70)
print("ALL TABLES IN ICEBERG CATALOG")
print("=" * 70)

for ns_row in spark.sql("SHOW NAMESPACES IN iceberg").collect():
    ns = ns_row[0]
    tables = spark.sql(f"SHOW TABLES IN iceberg.{ns}").collect()
    print(f"\niceberg.{ns}:")
    for t in tables:
        print(f"  - {t[1]}")

# ============================================================
# 2. CHECK IF OLD TABLES EXIST
# ============================================================
print("\n" + "=" * 70)
print("CHECKING OLD PIPELINE TABLES")
print("=" * 70)

old_tables = [
    "iceberg.bronze.data_referensi_mahasiswa",
    "iceberg.silver.silver_mahasiswa",
    "iceberg.silver.silver_khs",
    "iceberg.gold.dim_mahasiswa",
    "iceberg.gold.fact_khs",
    "iceberg.gold.data_referensi_mahasiswa",
    "iceberg.feature_store.feature_store_graduation_prediction",
    "iceberg.feature_store.training_dataset",
]

for table in old_tables:
    try:
        df = spark.table(table)
        count = df.count()
        print(f"  EXISTS: {table} ({count} rows)")
        # Check for target IDs
        for mid in TARGET_IDS:
            rows = df.filter(F.col("id_mahasiswa") == mid).collect() if "id_mahasiswa" in df.columns else []
            if not rows:
                rows = df.filter(F.col("id_mhs") == mid).collect() if "id_mhs" in df.columns else []
            if rows:
                r = rows[0]
                status = r.status_mahasiswa if "status_mahasiswa" in df.columns else "N/A"
                print(f"    {mid}: status={status}")
    except Exception as e:
        print(f"  NOT FOUND: {table}")

# ============================================================
# 3. CHECK dim_mahasiswa FOR AKTIF->LULUS ISSUE
# ============================================================
print("\n" + "=" * 70)
print("CHECK dim_mahasiswa STATUS DISTRIBUTION")
print("=" * 70)

try:
    dim = spark.table("iceberg.gold.dim_mahasiswa")
    print(f"dim_mahasiswa rows: {dim.count()}")
    print(f"dim_mahasiswa columns: {dim.columns}")
    
    print("\nStatus distribution:")
    for row in dim.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
        print(f"  {row.status_mahasiswa}: {row['count']}")
    
    # Check target IDs
    print("\nTarget IDs in dim_mahasiswa:")
    for mid in TARGET_IDS:
        rows = dim.filter(F.col("id_mahasiswa") == mid).collect()
        if rows:
            r = rows[0]
            print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}")
        else:
            print(f"  {mid}: NOT FOUND")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 4. CHECK silver_mahasiswa STATUS DISTRIBUTION
# ============================================================
print("\n" + "=" * 70)
print("CHECK silver_mahasiswa STATUS DISTRIBUTION")
print("=" * 70)

try:
    slv = spark.table("iceberg.silver.silver_mahasiswa")
    print(f"silver_mahasiswa rows: {slv.count()}")
    print(f"silver_mahasiswa columns: {slv.columns}")
    
    print("\nStatus distribution:")
    for row in slv.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
        print(f"  {row.status_mahasiswa}: {row['count']}")
    
    # Check target IDs
    print("\nTarget IDs in silver_mahasiswa:")
    for mid in TARGET_IDS:
        rows = slv.filter(F.col("id_mahasiswa") == mid).collect()
        if rows:
            r = rows[0]
            print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}")
        else:
            print(f"  {mid}: NOT FOUND")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 5. CHECK bronze.data_referensi_mahasiswa vs old bronze tables
# ============================================================
print("\n" + "=" * 70)
print("CHECK ALL BRONZE TABLES")
print("=" * 70)

try:
    brz = spark.table("iceberg.bronze.data_referensi_mahasiswa")
    print(f"bronze.data_referensi_mahasiswa rows: {brz.count()}")
    print(f"columns: {brz.columns}")
    
    print("\nStatus distribution:")
    for row in brz.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
        print(f"  {row.status_mahasiswa}: {row['count']}")
    
    # Check target IDs
    print("\nTarget IDs:")
    for mid in TARGET_IDS:
        rows = brz.filter(F.col("id_mhs") == mid).collect()
        if rows:
            r = rows[0]
            print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 6. CHECK GOLD for data_referensi_mahasiswa
# ============================================================
print("\n" + "=" * 70)
print("CHECK gold.data_referensi_mahasiswa STATUS")
print("=" * 70)

try:
    gld = spark.table("iceberg.gold.data_referensi_mahasiswa")
    print(f"gold.data_referensi_mahasiswa rows: {gld.count()}")
    print(f"columns: {gld.columns}")
    
    print("\nStatus distribution:")
    for row in gld.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
        print(f"  {row.status_mahasiswa}: {row['count']}")
    
    print("\nStatus kelulusan distribution:")
    for row in gld.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).collect():
        print(f"  {row.status_kelulusan}: {row['count']}")
    
    # Check target IDs
    print("\nTarget IDs:")
    for mid in TARGET_IDS:
        rows = gld.filter(F.col("id_mhs") == mid).collect()
        if rows:
            r = rows[0]
            print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}, label={r.status_kelulusan}")
except Exception as e:
    print(f"Error: {e}")

spark.stop()
print("\nOLD TABLES AUDIT COMPLETE")
