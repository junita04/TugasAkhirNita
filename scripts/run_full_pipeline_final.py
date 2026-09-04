import sys
sys.path.insert(0, '/opt/airflow')

print("=" * 80)
print("ML PIPELINE FINAL - END TO END")
print("=" * 80)

# Step 1: Rebuild Feature Store
print()
print("=" * 80)
print("STEP 1: REBUILD FEATURE STORE")
print("=" * 80)

from backend.feature_store.feature_store import run_feature_store
feature_store_report = run_feature_store()

# Step 2: Run ML Training
print()
print("=" * 80)
print("STEP 2: ML TRAINING")
print("=" * 80)

from backend.ml.evaluate import run_ml_pipeline
ml_result = run_ml_pipeline()

# Step 3: Run Inference
print()
print("=" * 80)
print("STEP 3: INFERENCE")
print("=" * 80)

from backend.ml.inference import run_inference
inference_result = run_inference(smoke_test=False)

# Step 4: Final Summary
print()
print("=" * 80)
print("ML PIPELINE FINAL")
print("=" * 80)

# Gold Layer
from backend.spark.session import get_spark
spark = get_spark('FinalSummary')
dim = spark.table('iceberg.gold.dim_mahasiswa')
gold_count = dim.count()

print()
print("GOLD")
print(f"Rows                 : {gold_count}")

# Feature Store
print()
print("FEATURE STORE")
fs_report = feature_store_report
print(f"Training sebelum     : {fs_report['training']['jumlah_awal_labeled']}")
print(f"Training IP NULL     : {fs_report['training']['jumlah_ip_null_dikeluarkan']}")
print(f"Training final       : {fs_report['training']['jumlah_valid']}")
print()
print(f"Inference sebelum    : {fs_report['inference']['jumlah_awal_aktif_2022_2024']}")
print(f"Inference IP NULL    : {fs_report['inference']['jumlah_ip_null_dikeluarkan']}")
print(f"Inference final      : {fs_report['inference']['jumlah_valid']}")

# Model
print()
print("MODEL")
print("GaussianNB No SMOTE")
print(f"CV Accuracy          : {ml_result['without_smote']['result']['cv_summary']['accuracy']['mean']:.4f}")
print(f"Accuracy             : {ml_result['without_smote']['result']['holdout']['accuracy']:.4f}")
print(f"Precision            : {ml_result['without_smote']['result']['holdout']['precision']:.4f}")
print(f"Recall               : {ml_result['without_smote']['result']['holdout']['recall']:.4f}")
print(f"F1 Score             : {ml_result['without_smote']['result']['holdout']['f1']:.4f}")

print()
print("GaussianNB SMOTE")
print(f"CV Accuracy          : {ml_result['with_smote']['result']['cv_summary']['accuracy']['mean']:.4f}")
print(f"Accuracy             : {ml_result['with_smote']['result']['holdout']['accuracy']:.4f}")
print(f"Precision            : {ml_result['with_smote']['result']['holdout']['precision']:.4f}")
print(f"Recall               : {ml_result['with_smote']['result']['holdout']['recall']:.4f}")
print(f"F1 Score             : {ml_result['with_smote']['result']['holdout']['f1']:.4f}")

# Inference Distribution
print()
print("INFERENCE DISTRIBUTION")

import pandas as pd
pred_no_smote = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_without_smote.parquet')
pred_smote = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_with_smote.parquet')

print()
print("Tanpa SMOTE")
tw_no_smote = (pred_no_smote['prediksi_label'] == 0).sum()
tl_no_smote = (pred_no_smote['prediksi_label'] == 1).sum()
total_no_smote = len(pred_no_smote)
print(f"Tepat Waktu          : {tw_no_smote} ({tw_no_smote/total_no_smote*100:.2f}%)")
print(f"Terlambat            : {tl_no_smote} ({tl_no_smote/total_no_smote*100:.2f}%)")

print()
print("Dengan SMOTE")
tw_smote = (pred_smote['prediksi_label'] == 0).sum()
tl_smote = (pred_smote['prediksi_label'] == 1).sum()
total_smote = len(pred_smote)
print(f"Tepat Waktu          : {tw_smote} ({tw_smote/total_smote*100:.2f}%)")
print(f"Terlambat            : {tl_smote} ({tl_smote/total_smote*100:.2f}%)")

# Distribution by Angkatan
print()
print("DISTRIBUSI PER ANGKATAN")

print()
print("Tanpa SMOTE")
print(f"{'Angkatan':<10} {'Tepat Waktu':>12} {'Terlambat':>12} {'Total':>8} {'% TW':>8} {'% TL':>8}")
print("-" * 60)
for angkatan in [2022, 2023, 2024]:
    subset = pred_no_smote[pred_no_smote['angkatan'] == angkatan]
    tw = (subset['prediksi_label'] == 0).sum()
    tl = (subset['prediksi_label'] == 1).sum()
    total = len(subset)
    pct_tw = tw/total*100 if total > 0 else 0
    pct_tl = tl/total*100 if total > 0 else 0
    print(f"{angkatan:<10} {tw:>12} {tl:>12} {total:>8} {pct_tw:>7.2f}% {pct_tl:>7.2f}%")
print("-" * 60)
print(f"{'TOTAL':<10} {tw_no_smote:>12} {tl_no_smote:>12} {total_no_smote:>8} {tw_no_smote/total_no_smote*100:>7.2f}% {tl_no_smote/total_no_smote*100:>7.2f}%")

print()
print("Dengan SMOTE")
print(f"{'Angkatan':<10} {'Tepat Waktu':>12} {'Terlambat':>12} {'Total':>8} {'% TW':>8} {'% TL':>8}")
print("-" * 60)
for angkatan in [2022, 2023, 2024]:
    subset = pred_smote[pred_smote['angkatan'] == angkatan]
    tw = (subset['prediksi_label'] == 0).sum()
    tl = (subset['prediksi_label'] == 1).sum()
    total = len(subset)
    pct_tw = tw/total*100 if total > 0 else 0
    pct_tl = tl/total*100 if total > 0 else 0
    print(f"{angkatan:<10} {tw:>12} {tl:>12} {total:>8} {pct_tw:>7.2f}% {pct_tl:>7.2f}%")
print("-" * 60)
print(f"{'TOTAL':<10} {tw_smote:>12} {tl_smote:>12} {total_smote:>8} {tw_smote/total_smote*100:>7.2f}% {tl_smote/total_smote*100:>7.2f}%")

# Validation
print()
print("VALIDASI JUMLAH DATA")
print(f"Total prediksi no smoke == Total inference: {total_no_smote == fs_report['inference']['jumlah_valid']}")
print(f"Total prediksi smote == Total inference: {total_smote == fs_report['inference']['jumlah_valid']}")

spark.stop()

print()
print("=" * 80)
print("PIPELINE SELESAI")
print("=" * 80)
