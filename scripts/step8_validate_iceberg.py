"""
STEP 8: VALIDATE ICEBERG
========================
Reads back all Iceberg tables and validates.
"""

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("validate_iceberg")
    .master("local[*]")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hive")
    .config("spark.sql.catalog.iceberg.uri", "thrift://hive-metastore:9083")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

tables = [
    "iceberg.gold.model_metrics",
    "iceberg.gold.confusion_matrix",
    "iceberg.gold.classification_report",
    "iceberg.gold.prediction_by_angkatan",
    "iceberg.gold.model_predictions",
]

print("=" * 70)
print("ICEBERG VALIDATION")
print("=" * 70)

all_ok = True

for table in tables:
    try:
        df = spark.table(table)
        count = df.count()
        print(f"  {table}: {count} rows - OK")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")
        all_ok = False

# Validate model_predictions
print()
print("--- model_predictions validation ---")
pred_df = spark.table("iceberg.gold.model_predictions")
total = pred_df.count()
print(f"  Total rows: {total}")

id_count = pred_df.groupBy("id_mhs").count().filter("count > 1").count()
print(f"  Duplicate IDs: {id_count}")
if id_count > 0:
    all_ok = False

preds = pred_df.select("prediksi").distinct().collect()
pred_vals = [r["prediksi"] for r in preds]
print(f"  Unique predictions: {pred_vals}")
valid_preds = all(p in ["Tepat Waktu", "Terlambat"] for p in pred_vals)
print(f"  All valid: {valid_preds}")
if not valid_preds:
    all_ok = False

null_ang = pred_df.filter(pred_df["angkatan"].isNull()).count()
print(f"  NULL angkatan: {null_ang}")
if null_ang > 0:
    all_ok = False

null_feat = pred_df.filter(pred_df["ip"].isNull()).count()
print(f"  NULL ip: {null_feat}")

# Validate prediction_by_angkatan
print()
print("--- prediction_by_angkatan validation ---")
pa_df = spark.table("iceberg.gold.prediction_by_angkatan")
pa_df.orderBy("angkatan").show(20, truncate=False)
pa_count = pa_df.count()
print(f"  Total angkatan: {pa_count}")

ang2023 = pa_df.filter(pa_df["angkatan"] == 2023).collect()
if ang2023:
    r = ang2023[0]
    print(f"  2023: total={r['total_mahasiswa']}, TW={r['prediksi_tepat_waktu']}, TL={r['prediksi_terlambat']}")
    assert r["prediksi_tepat_waktu"] == 3969, f"FAIL: expected 3969, got {r['prediksi_tepat_waktu']}"
    assert r["prediksi_terlambat"] == 16, f"FAIL: expected 16, got {r['prediksi_terlambat']}"
    print("  2023 validation: OK")

# Validate 3 target IDs
print()
print("--- 3 Mahasiswa audit validation ---")
target_ids = ["MHS000063", "MHS000361", "MHS024954"]
for tid in target_ids:
    row = pred_df.filter(pred_df["id_mhs"] == tid).collect()
    if row:
        r = row[0]
        print(f"  {tid}: pred={r['prediksi']}, prob_TW={r['probability_tepat_waktu']:.4f}")
        assert r["prediksi"] == "Tepat Waktu", f"FAIL: {tid} = {r['prediksi']}"
    else:
        print(f"  {tid}: NOT FOUND - FAIL")
        all_ok = False
print("  3 mahasiswa audit: OK")

# Validate features
print()
print("--- feature validation ---")
expected_cols = ["id_mhs", "jenis_kelamin", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks", "prediksi", "probability_tepat_waktu", "probability_terlambat"]
actual_cols = pred_df.columns
print(f"  Expected columns: {expected_cols}")
print(f"  Actual columns:   {actual_cols}")
cols_ok = set(expected_cols).issubset(set(actual_cols))
print(f"  Columns OK: {cols_ok}")
if not cols_ok:
    all_ok = False

print()
if all_ok:
    print("ALL VALIDATION PASSED!")
else:
    print("VALIDATION FAILED - check errors above")

spark.stop()
