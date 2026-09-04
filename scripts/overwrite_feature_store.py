"""
Overwrite old Feature Store tables with _fix data using Spark.
This makes the data visible in Trino.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (SparkSession.builder
    .appName("OverwriteFeatureStore")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hadoop")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.jars", "/opt/airflow/jars/iceberg-spark-runtime-3.5_2.12-1.5.2.jar,/opt/airflow/jars/hadoop-aws-3.3.4.jar,/opt/airflow/jars/aws-java-sdk-bundle-1.12.261.jar")
    .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")

print("=" * 70)
print("OVERWRITE OLD FEATURE STORE TABLES WITH _fix DATA")
print("=" * 70)

# Read _fix tables
train_fix = spark.table("iceberg.feature_store.training_dataset_fix")
inf_fix = spark.table("iceberg.feature_store.inference_dataset_fix")

train_count = train_fix.count()
inf_count = inf_fix.count()

print(f"\n_fix training_dataset_fix: {train_count} rows")
print(f"_fix inference_dataset_fix: {inf_count} rows")

# Overwrite old tables
print("\nOverwriting iceberg.feature_store.training_dataset...")
train_fix.writeTo("iceberg.feature_store.training_dataset").using("iceberg").createOrReplace()
print(f"  Done: {spark.table('iceberg.feature_store.training_dataset').count()} rows")

print("\nOverwriting iceberg.feature_store.inference_dataset...")
inf_fix.writeTo("iceberg.feature_store.inference_dataset").using("iceberg").createOrReplace()
print(f"  Done: {spark.table('iceberg.feature_store.inference_dataset').count()} rows")

# Verify
print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

for table in ["iceberg.gold.dim_mahasiswa", "iceberg.gold.fact_khs", 
              "iceberg.feature_store.training_dataset", "iceberg.feature_store.inference_dataset"]:
    c = spark.table(table).count()
    print(f"  {table}: {c} rows")

spark.stop()
print("\nDONE.")
