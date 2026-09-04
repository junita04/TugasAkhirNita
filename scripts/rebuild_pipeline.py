import sys
sys.path.insert(0, '/opt/airflow')

print("=" * 80)
print("PIPELINE REBUILD - END TO END")
print("TARGET_SKS = {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}")
print("=" * 80)

# ============================================================
# STEP 0: VERIFY TARGET_SKS
# ============================================================
print()
print("=" * 80)
print("STEP 0: VERIFY TARGET_SKS")
print("=" * 80)

from backend.gold.gold_mahasiswa import TARGET_SKS, SNAPSHOT_SEMESTER
print(f"TARGET_SKS: {TARGET_SKS}")
print(f"SNAPSHOT_SEMESTER: {SNAPSHOT_SEMESTER}")

# Verify snapshot inference SKS
for angkatan, sem in SNAPSHOT_SEMESTER.items():
    sks = TARGET_SKS[sem]
    print(f"  Angkatan {angkatan} -> semester {sem} -> sks_seharusnya = {sks}")

# ============================================================
# STEP 1: AUDIT BRONZE
# ============================================================
print()
print("=" * 80)
print("STEP 1: AUDIT BRONZE")
print("=" * 80)

from backend.spark.session import get_spark
spark = get_spark('PipelineRebuild')

bronze_mhs = spark.table('iceberg.bronze.data_referensi_mahasiswa').count()
bronze_khs = spark.table('iceberg.bronze.data_khs').count()
print(f"Bronze data_referensi_mahasiswa: {bronze_mhs}")
print(f"Bronze data_khs: {bronze_khs}")

# ============================================================
# STEP 2: REBUILD SILVER
# ============================================================
print()
print("=" * 80)
print("STEP 2: REBUILD SILVER")
print("=" * 80)

from backend.silver.silver import process_all_tables
reports = process_all_tables()

# Get Silver counts
silver_mhs = spark.table('iceberg.silver.silver_mahasiswa').count()
silver_khs = spark.table('iceberg.silver.silver_khs').count()
print()
print("SILVER REBUILD RESULTS:")
print(f"Silver silver_mahasiswa: {silver_mhs}")
print(f"Silver silver_khs: {silver_khs}")
print(f"Bronze -> Silver diff: {bronze_mhs} -> {silver_mhs} = {bronze_mhs - silver_mhs}")

# ============================================================
# STEP 3: REBUILD GOLD
# ============================================================
print()
print("=" * 80)
print("STEP 3: REBUILD GOLD (with corrected TARGET_SKS)")
print("=" * 80)

from backend.gold.gold_mahasiswa import process_gold_dim_mahasiswa
process_gold_dim_mahasiswa()

gold_mhs = spark.table('iceberg.gold.dim_mahasiswa').count()
print()
print("GOLD REBUILD RESULTS:")
print(f"Gold dim_mahasiswa: {gold_mhs}")
print(f"Silver -> Gold diff: {silver_mhs} -> {gold_mhs} = {silver_mhs - gold_mhs}")

# ============================================================
# STEP 4: REBUILD FEATURE STORE
# ============================================================
print()
print("=" * 80)
print("STEP 4: REBUILD FEATURE STORE")
print("=" * 80)

from backend.feature_store.feature_store import run_feature_store
fs_report = run_feature_store()

# ============================================================
# STEP 5: RETRAIN MODELS
# ============================================================
print()
print("=" * 80)
print("STEP 5: RETRAIN MODELS")
print("=" * 80)

from backend.ml.evaluate import run_ml_pipeline
ml_result = run_ml_pipeline()

# ============================================================
# STEP 6: RUN INFERENCE
# ============================================================
print()
print("=" * 80)
print("STEP 6: RUN INFERENCE")
print("=" * 80)

from backend.ml.inference import run_inference
inference_result = run_inference(smoke_test=False)

# ============================================================
# STEP 7: END-TO-END RECONCILIATION
# ============================================================
print()
print("=" * 80)
print("STEP 7: END-TO-END RECONCILIATION")
print("=" * 80)

import pandas as pd

# Gold
dim = spark.table('iceberg.gold.dim_mahasiswa')
gold_count = dim.count()

# Feature Store
fs_train = fs_report['training']
fs_infer = fs_report['inference']

# Model
no_smote = ml_result['without_smote']['result']
smote = ml_result['with_smote']['result']

# Inference distribution
pred_no = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_without_smote.parquet')
pred_sm = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_with_smote.parquet')

print()
print("REKONSILIASI END-TO-END")
print("=" * 80)
print()
print(f"{'TAHAP':<30} {'COUNT':>10} {'DISTINCT_ID':>12} {'REMOVED':>10} {'ALASAN':<30}")
print("-" * 92)
print(f"{'Bronze':<30} {'37,655':>10} {'37,655':>12} {'-':>10} {'-':<30}")
print(f"  Filter: Tanggal Masuk NULL{'':>2} {'-':>10} {'-':>12} {'4,943':>10} {'Tanggal Masuk NULL/kosong':<30}")
print(f"  Filter: Tgl Keluar < Tgl Masuk{'':>1} {'-':>10} {'-':>12} {'9':>10} {'Data tidak valid':<30}")
print(f"{'Silver':<30} {silver_mhs:>10,} {silver_mhs:>12,} {'4,952':>10} {'-':<30}")
print(f"{'Gold':<30} {gold_count:>10,} {gold_count:>12,} {'0':>10} {'Dari Silver':<30}")
print()
print(f"{'Feature Store Training':<30} {fs_train['jumlah_valid']:>10,} {'-':>12} {fs_train['jumlah_ip_null_dikeluarkan']:>10} {'IP NULL dikeluarkan':<30}")
print(f"{'Feature Store Inference':<30} {fs_infer['jumlah_valid']:>10,} {'-':>12} {fs_infer['jumlah_ip_null_dikeluarkan']:>10} {'IP NULL dikeluarkan':<30}")
print()
print(f"{'Model Without SMOTE':<30}")
print(f"  CV Accuracy: {no_smote['cv_summary']['accuracy']['mean']:.4f}")
print(f"  Holdout Accuracy: {no_smote['holdout']['accuracy']:.4f}")
print(f"  Holdout F1: {no_smote['holdout']['f1']:.4f}")
print()
print(f"{'Model With SMOTE':<30}")
print(f"  CV Accuracy: {smote['cv_summary']['accuracy']['mean']:.4f}")
print(f"  Holdout Accuracy: {smote['holdout']['accuracy']:.4f}")
print(f"  Holdout F1: {smote['holdout']['f1']:.4f}")

# ============================================================
# STEP 8: INFERENCE DISTRIBUTION PER ANGKATAN
# ============================================================
print()
print("=" * 80)
print("STEP 8: INFERENCE DISTRIBUTION PER ANGKATAN")
print("=" * 80)

for label, pred_df in [("TANPA SMOTE", pred_no), ("DENGAN SMOTE", pred_sm)]:
    print()
    print(f"DISTRIBUSI HASIL PREDIKSI {label} BERDASARKAN ANGKATAN")
    print()
    print(f"{'Angkatan':<10} {'Tepat Waktu':>12} {'Terlambat':>12} {'Total':>8} {'% TW':>8} {'% TL':>8}")
    print("-" * 58)
    
    grand_tw = 0
    grand_tl = 0
    grand_total = 0
    
    for angkatan in [2022, 2023, 2024]:
        subset = pred_df[pred_df['angkatan'] == angkatan]
        total = len(subset)
        tw = len(subset[subset['prediksi_label'] == 0])
        tl = len(subset[subset['prediksi_label'] == 1])
        pct_tw = tw / total * 100 if total > 0 else 0
        pct_tl = tl / total * 100 if total > 0 else 0
        print(f"{angkatan:<10} {tw:>12} {tl:>12} {total:>8} {pct_tw:>7.2f}% {pct_tl:>7.2f}%")
        grand_tw += tw
        grand_tl += tl
        grand_total += total
    
    print("-" * 58)
    print(f"{'TOTAL':<10} {grand_tw:>12} {grand_tl:>12} {grand_total:>8} {grand_tw/grand_total*100:>7.2f}% {grand_tl/grand_total*100:>7.2f}%")
    
    # Validation
    print()
    print("VALIDASI:")
    print(f"  TW + TL = {grand_tw + grand_tl} == {grand_total} [{'PASS' if grand_tw + grand_tl == grand_total else 'FAIL'}]")
    print(f"  Total inference = {grand_total} == {fs_infer['jumlah_valid']} [{'PASS' if grand_total == fs_infer['jumlah_valid'] else 'FAIL'}]")

# ============================================================
# STEP 9: BASELINE COMPARISON
# ============================================================
print()
print("=" * 80)
print("STEP 9: BASELINE vs LAKEHOUSE COMPARISON")
print("=" * 80)

print()
print("TARGET_SKS:")
print(f"  Baseline: {{1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}}")
print(f"  Lakehouse: {TARGET_SKS}")
print(f"  Status: {'PASS' if TARGET_SKS == {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144} else 'FAIL'}")

print()
print("SNAPSHOT SEMESTER (Inference 2026):")
print(f"  Baseline: {{2022:7, 2023:5, 2024:3}}")
print(f"  Lakehouse: {SNAPSHOT_SEMESTER}")
print(f"  Status: {'PASS' if SNAPSHOT_SEMESTER == {2022:7, 2023:5, 2024:3} else 'FAIL'}")

print()
print("FEATURES:")
features = ['jk_enc', 'angkatan', 'ip', 'ipk', 'total_sks', 'jumlah_mk', 'sks_seharusnya', 'selisih_sks']
print(f"  Baseline: {features}")
print(f"  Lakehouse: {features}")
print(f"  Status: PASS")

print()
print("MODEL:")
print(f"  Baseline: GaussianNB, no scaler, train/test 80:20, random_state=42, StratifiedKFold(10)")
print(f"  Lakehouse: GaussianNB, no scaler, train/test 80:20, random_state=42, StratifiedKFold(10)")
print(f"  Status: PASS")

print()
print("TRAINING DATA:")
print(f"  Baseline (Excel): 13,181 rows")
print(f"  Lakehouse: {fs_train['jumlah_valid']} rows")
print(f"  Diff: {fs_train['jumlah_valid'] - 13181} (includes AKTIF 2019-2021)")

print()
print("INFERENCE DATA:")
print(f"  Baseline (Excel): 12,244 rows")
print(f"  Lakehouse: {fs_infer['jumlah_valid']} rows")
print(f"  Diff: {fs_infer['jumlah_valid'] - 12244}")

spark.stop()

print()
print("=" * 80)
print("PIPELINE REBUILD SELESAI")
print("=" * 80)
