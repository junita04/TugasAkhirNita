"""
STEP 7: SAVE TO ICEBERG
=======================
Creates gold.model_metrics, gold.confusion_matrix, gold.classification_report,
gold.prediction_by_angkatan, gold.model_predictions using the iceberg catalog.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType, IntegerType, StringType, StructField, StructType,
)

spark = (
    SparkSession.builder
    .appName("save_results_to_iceberg")
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
    .config("spark.eventLog.enabled", "true")
    .config("spark.eventLog.dir", "file:///spark-events")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# =========================================================================
# 7a: gold.model_metrics
# =========================================================================
print("7a: Creating gold.model_metrics ...")
metrics_schema = StructType([
    StructField("model", StringType()),
    StructField("cv_mean_accuracy", DoubleType()),
    StructField("cv_std_accuracy", DoubleType()),
    StructField("cv_mean_f1", DoubleType()),
    StructField("cv_std_f1", DoubleType()),
    StructField("test_accuracy", DoubleType()),
    StructField("test_precision", DoubleType()),
    StructField("test_recall", DoubleType()),
    StructField("test_f1", DoubleType()),
    StructField("training_samples", IntegerType()),
    StructField("test_samples", IntegerType()),
    StructField("inference_samples", IntegerType()),
    StructField("features_count", IntegerType()),
    StructField("pipeline_version", StringType()),
    StructField("training_date", StringType()),
])
metrics_data = [(
    "GaussianNB",
    0.7439502727154544, 0.011587594960355439,
    0.7570081247320404, 0.010847861250127648,
    0.7383390216154722, 0.7766957746223667,
    0.7383390216154722, 0.7512063384783562,
    13181, 2637, 14662,
    8, "v2", "2026-08-27T04:17:33",
)]
metrics_df = spark.createDataFrame(metrics_data, schema=metrics_schema)
spark.sql("CREATE SCHEMA IF NOT EXISTS iceberg.gold")
metrics_df.writeTo("iceberg.gold.model_metrics").createOrReplace()
print(f"  gold.model_metrics: {metrics_df.count()} rows")

# =========================================================================
# 7b: gold.confusion_matrix
# =========================================================================
print("7b: Creating gold.confusion_matrix ...")
cm_schema = StructType([
    StructField("actual", StringType()),
    StructField("predicted", StringType()),
    StructField("count", IntegerType()),
])
cm_data = [
    ("Tepat Waktu", "Tepat Waktu", 410),
    ("Tepat Waktu", "Terlambat", 221),
    ("Terlambat", "Tepat Waktu", 469),
    ("Terlambat", "Terlambat", 1537),
]
cm_df = spark.createDataFrame(cm_data, schema=cm_schema)
cm_df.writeTo("iceberg.gold.confusion_matrix").createOrReplace()
print(f"  gold.confusion_matrix: {cm_df.count()} rows")

# =========================================================================
# 7c: gold.classification_report
# =========================================================================
print("7c: Creating gold.classification_report ...")
cr_schema = StructType([
    StructField("class", StringType()),
    StructField("precision", DoubleType()),
    StructField("recall", DoubleType()),
    StructField("f1_score", DoubleType()),
    StructField("support", IntegerType()),
])
cr_data = [
    ("Tepat Waktu", 0.47, 0.65, 0.54, 631),
    ("Terlambat", 0.87, 0.77, 0.82, 2006),
    ("weighted_avg", 0.78, 0.74, 0.75, 2637),
]
cr_df = spark.createDataFrame(cr_data, schema=cr_schema)
cr_df.writeTo("iceberg.gold.classification_report").createOrReplace()
print(f"  gold.classification_report: {cr_df.count()} rows")

# =========================================================================
# 7d: gold.prediction_by_angkatan
# =========================================================================
print("7d: Creating gold.prediction_by_angkatan ...")
pa_schema = StructType([
    StructField("angkatan", IntegerType()),
    StructField("total_mahasiswa", IntegerType()),
    StructField("prediksi_tepat_waktu", IntegerType()),
    StructField("prediksi_terlambat", IntegerType()),
    StructField("persentase_tepat_waktu", DoubleType()),
    StructField("persentase_terlambat", DoubleType()),
])
pa_data = [
    (2019, 317, 4, 313, 1.26, 98.74),
    (2020, 783, 16, 767, 2.04, 97.96),
    (2021, 1318, 112, 1206, 8.50, 91.50),
    (2022, 3987, 548, 3439, 13.74, 86.26),
    (2023, 3985, 3969, 16, 99.60, 0.40),
    (2024, 4272, 4272, 0, 100.00, 0.00),
]
pa_df = spark.createDataFrame(pa_data, schema=pa_schema)
pa_df.writeTo("iceberg.gold.prediction_by_angkatan").createOrReplace()
print(f"  gold.prediction_by_angkatan: {pa_df.count()} rows")

# =========================================================================
# 7e: gold.model_predictions
# =========================================================================
print("7e: Creating gold.model_predictions ...")
import pandas as pd
pred_pdf = pd.read_csv("/opt/airflow/output/prediction_mahasiswa_aktif.csv")
pred_pdf = pred_pdf.fillna("")

pred_pdf = pred_pdf.rename(columns={
    "prob_tepat_waktu": "probability_tepat_waktu",
    "prob_terlambat": "probability_terlambat",
})

pred_spark = spark.createDataFrame(pred_pdf)
pred_spark = pred_spark.withColumn("probability_tepat_waktu", pred_spark["probability_tepat_waktu"].cast(DoubleType()))
pred_spark = pred_spark.withColumn("probability_terlambat", pred_spark["probability_terlambat"].cast(DoubleType()))
pred_spark.writeTo("iceberg.gold.model_predictions").createOrReplace()
print(f"  gold.model_predictions: {pred_spark.count()} rows")

spark.stop()
print()
print("STEP 7 COMPLETE: All tables saved to Iceberg")
