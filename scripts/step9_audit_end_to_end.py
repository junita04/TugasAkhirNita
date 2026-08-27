"""
STEP 9: AUDIT END-TO-END
=========================
Checks status consistency across all layers.
"""

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("audit_end_to_end")
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

target_ids = ["MHS000063", "MHS000361", "MHS024954"]

print("=" * 70)
print("END-TO-END AUDIT")
print("=" * 70)

# 1. Source (Excel)
print()
print("1. SOURCE (Excel)")
src = (spark.read.format("excel")
    .option("header", True)
    .load("/opt/airflow/data/(asli)req_data_rut (1).xlsx"))
src_cols = src.columns
print(f"  Source columns: {src_cols}")
# Find status column (may have different casing)
status_col = [c for c in src_cols if "status" in c.lower()][0]
tgl_col = [c for c in src_cols if "tanggal" in c.lower() and "keluar" in c.lower()][0]
id_col = [c for c in src_cols if "id" in c.lower() and "mhs" in c.lower()][0]
print(f"  Using: id={id_col}, status={status_col}, tgl_keluar={tgl_col}")

src_target = src.filter(src[id_col].isin(target_ids)).select(
    id_col, status_col, tgl_col).collect()
for r in src_target:
    print(f"  {r[id_col]}: status={r[status_col]}, tgl_keluar={r[tgl_col]}")
src_lulus = src.filter(src[status_col] == "Lulus").count()
src_aktif = src.filter(src[status_col] == "AKTIF").count()
print(f"  Total: {src.count()}, Lulus: {src_lulus}, AKTIF: {src_aktif}")

# 2. Bronze
print()
print("2. BRONZE")
bz = spark.table("iceberg.bronze.data_referensi_mahasiswa")
bz_target = bz.filter(bz["id_mhs"].isin(target_ids)).select(
    "id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in bz_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
print(f"  Total: {bz.count()} rows")

# 3. Silver
print()
print("3. SILVER")
sl = spark.table("iceberg.silver.data_referensi_mahasiswa")
sl_target = sl.filter(sl["id_mhs"].isin(target_ids)).select(
    "id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in sl_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
print(f"  Total: {sl.count()} rows")

# 4. Gold
print()
print("4. GOLD")
gd = spark.table("iceberg.gold.data_referensi_mahasiswa")
gd_target = gd.filter(gd["id_mhs"].isin(target_ids)).select(
    "id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in gd_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
print(f"  Total: {gd.count()} rows")

# 5. Feature Store
print()
print("5. FEATURE STORE")
fs = spark.table("iceberg.feature_store.training_kelulusan")
print(f"  Training: {fs.count()} rows")
fs2 = spark.table("iceberg.feature_store.inference_mahasiswa_aktif")
print(f"  Inference: {fs2.count()} rows")

# 6. Gold model tables
print()
print("6. GOLD MODEL TABLES")
for t in ["model_metrics", "confusion_matrix", "classification_report", "prediction_by_angkatan", "model_predictions"]:
    try:
        df = spark.table(f"iceberg.gold.{t}")
        print(f"  iceberg.gold.{t}: {df.count()} rows")
    except Exception as e:
        print(f"  iceberg.gold.{t}: ERROR - {e}")

# 7. Predictions
print()
print("7. PREDICTIONS")
pred = spark.table("iceberg.gold.model_predictions")
pred_target = pred.filter(pred["id_mhs"].isin(target_ids)).collect()
for r in pred_target:
    print(f"  {r['id_mhs']}: pred={r['prediksi']}, prob_TW={r['probability_tepat_waktu']:.4f}")

# 8. Check status consistency
print()
print("8. STATUS CONSISTENCY CHECK")
all_ok = True
for tid in target_ids:
    src_s = src.filter(src[id_col] == tid).select(status_col).collect()[0][status_col]
    bz_s = bz.filter(bz["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    sl_s = sl.filter(sl["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    gd_s = gd.filter(gd["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    consistent = src_s == bz_s == sl_s == gd_s == "AKTIF"
    print(f"  {tid}: src={src_s}, bz={bz_s}, sl={sl_s}, gd={gd_s} -> {'OK' if consistent else 'FAIL'}")
    if not consistent:
        all_ok = False

# 9. Summary
print()
print("=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)
print(f"  Source total:        {src.count()}")
print(f"  Bronze total:        {bz.count()}")
print(f"  Silver total:        {sl.count()}")
print(f"  Gold total:          {gd.count()}")
print(f"  Training (FS):       {fs.count()}")
print(f"  Inference (FS):      {fs2.count()}")
print(f"  Predictions:         {pred.count()}")
print(f"  Target IDs AKTIF:    {'OK' if all_ok else 'FAIL'}")
print(f"  Status consistent:   {'OK' if all_ok else 'FAIL'}")

spark.stop()
print()
print("AUDIT COMPLETE")
