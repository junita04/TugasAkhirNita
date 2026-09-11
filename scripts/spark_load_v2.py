"""
Phase 2-5: Spark writes Parquet -> Iceberg tables.
Uses shared /opt/airflow/data/parquet_v2/ location.
"""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark
import pyspark.sql.functions as F

PARQUET_DIR = "/opt/airflow/data/parquet_v2"

print("=" * 70)
print("PHASE 2-5: SPARK -> ICEBERG")
print("=" * 70)

spark = get_spark("Load V2 Data")

# =====================================================
# PHASE 2: training_dataset_v2
# =====================================================
print("\n" + "=" * 70)
print("PHASE 2: LOADING training_dataset_v2")
print("=" * 70)

train_path = f"{PARQUET_DIR}/training_dataset_v2"
df_train = spark.read.parquet(train_path)
print(f"  Read from parquet: {df_train.count()} rows")
df_train.printSchema()

TABLE_TRAIN = "hive_iceberg.feature_store.training_dataset_v2"
df_train.writeTo(TABLE_TRAIN).using("iceberg").createOrReplace()
print(f"  Written to: {TABLE_TRAIN}")

cnt = spark.table(TABLE_TRAIN).count()
print(f"  Validation count: {cnt}")
assert cnt == 15505, f"Expected 15505, got {cnt}"
print("  Label distribution:")
spark.table(TABLE_TRAIN).groupBy("label").count().show()
print("  PASS: training_dataset_v2")

# =====================================================
# PHASE 3: inference_dataset_v2
# =====================================================
print("\n" + "=" * 70)
print("PHASE 3: LOADING inference_dataset_v2")
print("=" * 70)

infer_path = f"{PARQUET_DIR}/inference_dataset_v2"
df_infer = spark.read.parquet(infer_path)
print(f"  Read from parquet: {df_infer.count()} rows")
df_infer.printSchema()

TABLE_INFER = "hive_iceberg.feature_store.inference_dataset_v2"
df_infer.writeTo(TABLE_INFER).using("iceberg").createOrReplace()
print(f"  Written to: {TABLE_INFER}")

cnt = spark.table(TABLE_INFER).count()
print(f"  Validation count: {cnt}")
assert cnt == 12338, f"Expected 12338, got {cnt}"
print("  PASS: inference_dataset_v2")

# =====================================================
# PHASE 4: model_predictions_v2
# =====================================================
print("\n" + "=" * 70)
print("PHASE 4: LOADING model_predictions_v2")
print("=" * 70)

pred_path = f"{PARQUET_DIR}/model_predictions_v2"
df_pred = spark.read.parquet(pred_path)
print(f"  Read from parquet: {df_pred.count()} rows")
df_pred.printSchema()

TABLE_PRED = "hive_iceberg.gold.model_predictions_v2"
df_pred.writeTo(TABLE_PRED).using("iceberg").createOrReplace()
print(f"  Written to: {TABLE_PRED}")

cnt = spark.table(TABLE_PRED).count()
print(f"  Validation count: {cnt}")
assert cnt == 12338, f"Expected 12338, got {cnt}"
print("  Prediction distribution:")
spark.table(TABLE_PRED).groupBy("Prediksi_Label").count().show()
print("  PASS: model_predictions_v2")

# =====================================================
# PHASE 5: prediction_by_angkatan_v2
# =====================================================
print("\n" + "=" * 70)
print("PHASE 5: CREATING prediction_by_angkatan_v2")
print("=" * 70)

df_agg = (
    df_pred
    .groupBy("angkatan")
    .agg(
        F.count("*").alias("total_mahasiswa"),
        F.sum(F.when(F.col("Prediksi") == 0, 1).otherwise(0)).alias("prediksi_tepat_waktu"),
        F.sum(F.when(F.col("Prediksi") == 1, 1).otherwise(0)).alias("prediksi_terlambat"),
    )
    .withColumn("persentase_tepat_waktu", F.round(F.col("prediksi_tepat_waktu") / F.col("total_mahasiswa") * 100, 2))
    .withColumn("persentase_terlambat", F.round(F.col("prediksi_terlambat") / F.col("total_mahasiswa") * 100, 2))
    .orderBy("angkatan")
)

print("  Aggregation result:")
df_agg.show()

total = df_agg.agg(F.sum("total_mahasiswa")).collect()[0][0]
print(f"  Total mahasiswa: {total}")
assert total == 12338, f"Expected 12338, got {total}"

TABLE_AGG = "hive_iceberg.gold.prediction_by_angkatan_v2"
df_agg.writeTo(TABLE_AGG).using("iceberg").createOrReplace()
print(f"  Written to: {TABLE_AGG}")

cnt = spark.table(TABLE_AGG).count()
print(f"  Validation count: {cnt}")
print("  PASS: prediction_by_angkatan_v2")

# =====================================================
# FINAL SUMMARY
# =====================================================
print("\n" + "=" * 70)
print("ALL PHASES COMPLETE")
print("=" * 70)
print(f"  training_dataset_v2: {spark.table(TABLE_TRAIN).count()} rows")
print(f"  inference_dataset_v2: {spark.table(TABLE_INFER).count()} rows")
print(f"  model_predictions_v2: {spark.table(TABLE_PRED).count()} rows")
print(f"  prediction_by_angkatan_v2: {spark.table(TABLE_AGG).count()} rows")
print("=" * 70)
