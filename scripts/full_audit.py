import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd
import numpy as np
from backend.spark.session import get_spark

spark = get_spark('FullAudit')

print("=" * 100)
print("COMPREHENSIVE ML PIPELINE AUDIT")
print("=" * 100)

# ============================================================
# 1. AUDIT DATA INFERENCE PER ANGKATAN
# ============================================================
print()
print("=" * 100)
print("1. AUDIT DATA INFERENCE PER ANGKATAN")
print("=" * 100)

gold = spark.table('iceberg.gold.dim_mahasiswa').toPandas()

# Inference: AKTIF 2022-2024
inference = gold[
    (gold['status_mahasiswa'].str.upper() == 'AKTIF') &
    (gold['angkatan'].isin([2022, 2023, 2024]))
].copy()

print()
print("TOTAL INFERENCE:", len(inference))
for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    print(f"  Angkatan {ang}: {len(subset)}")

print()
print("FEATURE STATS PER ANGKATAN:")
print()
header = f"{'Angkatan':<10} {'N':>6} {'Mean SKS':>10} {'Med SKS':>9} {'Min SKS':>9} {'Max SKS':>9} {'Mean IPK':>10} {'Mean Sem':>9} {'Mean SKS_S':>11} {'Mean Selisih':>13}"
print(header)
print("-" * len(header))

for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    n = len(subset)
    mean_sks = subset['total_sks'].mean()
    med_sks = subset['total_sks'].median()
    min_sks = subset['total_sks'].min()
    max_sks = subset['total_sks'].max()
    mean_ipk = subset['ipk'].mean()
    mean_sem = subset['semester'].mean()
    mean_sks_s = subset['sks_seharusnya'].mean()
    mean_sel = subset['selisih_sks'].mean()
    print(f"{ang:<10} {n:>6} {mean_sks:>10.2f} {med_sks:>9.0f} {min_sks:>9.0f} {max_sks:>9.0f} {mean_ipk:>10.4f} {mean_sem:>9.2f} {mean_sks_s:>11.2f} {mean_sel:>13.2f}")

print()
print("NULL CHECK PER ANGKATAN:")
print(f"{'Angkatan':<10} {'N':>6} {'IPK NULL':>10} {'TotalSKS NULL':>14} {'JmlMK NULL':>12} {'Semester NULL':>14}")
print("-" * 68)
for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    n = len(subset)
    ipk_null = subset['ipk'].isnull().sum()
    sks_null = subset['total_sks'].isnull().sum()
    mk_null = subset['jumlah_mk'].isnull().sum()
    sem_null = subset['semester'].isnull().sum()
    print(f"{ang:<10} {n:>6} {ipk_null:>10} {sks_null:>14} {mk_null:>12} {sem_null:>14}")

print()
print("SEMESTER DISTRIBUTION PER ANGKATAN:")
for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    sem_dist = subset['semester'].value_counts().sort_index()
    print(f"  Angkatan {ang}: {dict(sem_dist)}")

print()
print("SKS_SEHARUSNYA DISTRIBUTION PER ANGKATAN:")
for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    sks_dist = subset['sks_seharusnya'].value_counts().sort_index()
    print(f"  Angkatan {ang}: {dict(sks_dist)}")

# ============================================================
# 2. AUDIT PROBABILITY DISTRIBUTION PER ANGKATAN
# ============================================================
print()
print("=" * 100)
print("2. AUDIT PROBABILITY DISTRIBUTION PER ANGKATAN")
print("=" * 100)

pred_no = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_without_smote.parquet')
pred_sm = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_with_smote.parquet')

for label, pred_df in [("TANPA SMOTE", pred_no), ("DENGAN SMOTE", pred_sm)]:
    print()
    print(f"--- {label} ---")
    print()
    header = f"{'Angkatan':<10} {'N':>6} {'Pred TW':>8} {'Pred TL':>8} {'Min P(TW)':>11} {'Mean P(TW)':>12} {'Max P(TW)':>11} {'Med P(TW)':>11}"
    print(header)
    print("-" * len(header))
    
    for ang in [2022, 2023, 2024]:
        subset = pred_df[pred_df['angkatan'] == ang]
        n = len(subset)
        pred_tw = (subset['prediksi_label'] == 0).sum()
        pred_tl = (subset['prediksi_label'] == 1).sum()
        min_ptw = subset['probability_tepat_waktu'].min()
        mean_ptw = subset['probability_tepat_waktu'].mean()
        max_ptw = subset['probability_tepat_waktu'].max()
        med_ptw = subset['probability_tepat_waktu'].median()
        print(f"{ang:<10} {n:>6} {pred_tw:>8} {pred_tl:>8} {min_ptw:>11.6f} {mean_ptw:>12.6f} {max_ptw:>11.6f} {med_ptw:>11.6f}")

# ============================================================
# 3. AUDIT FEATURE DISTRIBUTION TRAINING VS INFERENCE
# ============================================================
print()
print("=" * 100)
print("3. AUDIT FEATURE DISTRIBUTION: TRAINING vs INFERENCE")
print("=" * 100)

# Training data
training_path = '/opt/airflow/logs/feature_store_quality_report.json'
training_fs = spark.table('iceberg.feature_store.training_dataset').toPandas()

FEATURES = ['jk_enc', 'angkatan', 'ip', 'ipk', 'total_sks', 'jumlah_mk', 'sks_seharusnya', 'selisih_sks']

print()
header = f"{'Feature':<16} {'Set':<16} {'Min':>10} {'Max':>10} {'Mean':>10} {'Median':>10} {'Std':>10}"
print(header)
print("-" * len(header))

for feat in FEATURES:
    # Training
    t = training_fs[feat]
    print(f"{feat:<16} {'Training':<16} {t.min():>10.4f} {t.max():>10.4f} {t.mean():>10.4f} {t.median():>10.4f} {t.std():>10.4f}")
    
    for ang in [2022, 2023, 2024]:
        subset = inference[inference['angkatan'] == ang]
        s = subset[feat]
        print(f"{'':<16} {f'Inference {ang}':<16} {s.min():>10.4f} {s.max():>10.4f} {s.mean():>10.4f} {s.median():>10.4f} {s.std():>10.4f}")
    print()

# ============================================================
# 4. AUDIT SELISIH SKS
# ============================================================
print()
print("=" * 100)
print("4. AUDIT SELISIH SKS")
print("=" * 100)

print()
header = f"{'Angkatan':<10} {'N':>6} {'Sel<0':>8} {'Sel=0':>8} {'Sel>0':>8} {'%Sel<0':>8}"
print(header)
print("-" * 50)

for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    n = len(subset)
    sel_neg = (subset['selisih_sks'] < 0).sum()
    sel_zero = (subset['selisih_sks'] == 0).sum()
    sel_pos = (subset['selisih_sks'] > 0).sum()
    pct_neg = sel_neg / n * 100 if n > 0 else 0
    print(f"{ang:<10} {n:>6} {sel_neg:>8} {sel_zero:>8} {sel_pos:>8} {pct_neg:>7.2f}%")

# Contoh data
print()
print("CONTOH: 10 Mahasiswa Angkatan 2023 dengan Selisih SKS Terbesar:")
subset_2023 = inference[inference['angkatan'] == 2023].copy()
top10 = subset_2023.nlargest(10, 'selisih_sks')
print(top10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip', 'semester']].to_string(index=False))

print()
print("CONTOH: 10 Mahasiswa Angkatan 2023 dengan Selisih SKS Terkecil:")
bottom10 = subset_2023.nsmallest(10, 'selisih_sks')
print(bottom10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip', 'semester']].to_string(index=False))

print()
print("CONTOH: 10 Mahasiswa Angkatan 2024 dengan Selisih SKS Terbesar:")
subset_2024 = inference[inference['angkatan'] == 2024].copy()
top10 = subset_2024.nlargest(10, 'selisih_sks')
print(top10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip', 'semester']].to_string(index=False))

print()
print("CONTOH: 10 Mahasiswa Angkatan 2024 dengan Selisih SKS Terkecil:")
bottom10 = subset_2024.nsmallest(10, 'selisih_sks')
print(bottom10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip', 'semester']].to_string(index=False))

# ============================================================
# 5. AUDIT SEMESTER CALCULATION
# ============================================================
print()
print("=" * 100)
print("5. AUDIT SEMESTER CALCULATION")
print("=" * 100)

print()
print("CONTOH 20 MAHASISWA INFERENCE:")
sample = inference.head(20)
print(sample[['id_mahasiswa', 'angkatan', 'tanggal_masuk', 'semester', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk']].to_string(index=False))

# ============================================================
# 6. AUDIT TRAINING DATA COMPOSITION
# ============================================================
print()
print("=" * 100)
print("6. AUDIT TRAINING DATA COMPOSITION")
print("=" * 100)

# All labeled students
labeled = gold[gold['label'].notna()].copy()

print()
print("DISTRIBUSI TRAINING PER ANGKATAN DAN STATUS:")
print()
header = f"{'Angkatan':<10} {'Status':<12} {'Label':<12} {'Jumlah':>8}"
print(header)
print("-" * 42)

for ang in sorted(labeled['angkatan'].unique()):
    for status in labeled[labeled['angkatan'] == ang]['status_mahasiswa'].unique():
        for label in [0, 1]:
            count = len(labeled[(labeled['angkatan'] == ang) & (labeled['status_mahasiswa'] == status) & (labeled['label'] == label)])
            if count > 0:
                label_name = "Tepat Waktu" if label == 0 else "Terlambat"
                print(f"{ang:<10} {status:<12} {label_name:<12} {count:>8}")

print()
print("cek apakah ada mahasiswa inference yang masuk training:")
inference_ids = set(inference['id_mahasiswa'].values)
training_ids = set(training_fs['id_mahasiswa'].values)
overlap = inference_ids & training_ids
print(f"  Inference IDs: {len(inference_ids)}")
print(f"  Training IDs: {len(training_ids)}")
print(f"  Overlap: {len(overlap)}")
if len(overlap) > 0:
    print(f"  WARNING: {len(overlap)} mahasiswa inference masuk training!")
    print(f"  Contoh: {list(overlap)[:10]}")
else:
    print("  PASS: Tidak ada overlap")

# ============================================================
# 7. AUDIT IPK NULL
# ============================================================
print()
print("=" * 100)
print("7. AUDIT IPK NULL")
print("=" * 100)

print()
print("TRAINING:")
print(f"  Sebelum filtering: {len(training_fs)}")
ipk_null_train = training_fs['ipk'].isnull().sum()
print(f"  IPK NULL: {ipk_null_train}")
print(f"  Sesudah filtering: {len(training_fs) - ipk_null_train}")

print()
print("INFERENCE:")
for ang in [2022, 2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    n = len(subset)
    ipk_null = subset['ipk'].isnull().sum()
    print(f"  Angkatan {ang}: sebelum={n}, IPK NULL={ipk_null}, sesudah={n - ipk_null}")

# ============================================================
# 8. AUDIT TARGET_SKS MAPPING
# ============================================================
print()
print("=" * 100)
print("8. AUDIT TARGET_SKS MAPPING")
print("=" * 100)

from backend.gold.gold_mahasiswa import TARGET_SKS, SNAPSHOT_SEMESTER

print()
print("TARGET_SKS yang digunakan:")
for sem, sks in sorted(TARGET_SKS.items()):
    print(f"  Semester {sem}: {sks} SKS")

print()
print("SNAPSHOT_SEMESTER:")
for ang, sem in sorted(SNAPSHOT_SEMESTER.items()):
    print(f"  Angkatan {ang}: semester {sem} -> {TARGET_SKS[sem]} SKS")

# ============================================================
# 9. DIAGNOSIS: WHY 0 TW FOR 2023/2024
# ============================================================
print()
print("=" * 100)
print("9. DIAGNOSIS: WHY 0 TEWAT WAKTU FOR 2023/2024")
print("=" * 100)

print()
print("ANALISIS PROBABILITAS:")
for ang in [2022, 2023, 2024]:
    subset = pred_no[pred_no['angkatan'] == ang]
    print(f"\nAngkatan {ang} ({len(subset)} mahasiswa):")
    print(f"  P(TW) min:    {subset['probability_tepat_waktu'].min():.6f}")
    print(f"  P(TW) mean:   {subset['probability_tepat_waktu'].mean():.6f}")
    print(f"  P(TW) median: {subset['probability_tepat_waktu'].median():.6f}")
    print(f"  P(TW) max:    {subset['probability_tepat_waktu'].max():.6f}")
    print(f"  P(TL) min:    {subset['probability_terlambat'].min():.6f}")
    print(f"  P(TL) mean:   {subset['probability_terlambat'].mean():.6f}")
    print(f"  P(TL) max:    {subset['probability_terlambat'].max():.6f}")
    
    # Check: how many have P(TW) > 0.5?
    high_ptw = (subset['probability_tepat_waktu'] > 0.5).sum()
    print(f"  P(TW) > 0.5:  {high_ptw}")

print()
print("FEATURE COMPARISON: Training TW vs Inference 2023/2024")
training_tw = training_fs[training_fs['label'] == 0]
training_tl = training_fs[training_fs['label'] == 1]

print()
print(f"Training TW (n={len(training_tw)}):")
print(f"  IPK  mean={training_tw['ipk'].mean():.4f}, std={training_tw['ipk'].std():.4f}")
print(f"  SKS  mean={training_tw['total_sks'].mean():.2f}, std={training_tw['total_sks'].std():.2f}")
print(f"  SKS_S mean={training_tw['sks_seharusnya'].mean():.2f}")
print(f"  Sel  mean={training_tw['selisih_sks'].mean():.2f}")

print()
print(f"Training TL (n={len(training_tl)}):")
print(f"  IPK  mean={training_tl['ipk'].mean():.4f}, std={training_tl['ipk'].std():.4f}")
print(f"  SKS  mean={training_tl['total_sks'].mean():.2f}, std={training_tl['total_sks'].std():.2f}")
print(f"  SKS_S mean={training_tl['sks_seharusnya'].mean():.2f}")
print(f"  Sel  mean={training_tl['selisih_sks'].mean():.2f}")

for ang in [2023, 2024]:
    subset = inference[inference['angkatan'] == ang]
    print()
    print(f"Inference {ang} (n={len(subset)}):")
    print(f"  IPK  mean={subset['ipk'].mean():.4f}, std={subset['ipk'].std():.4f}")
    print(f"  SKS  mean={subset['total_sks'].mean():.2f}, std={subset['total_sks'].std():.2f}")
    print(f"  SKS_S mean={subset['sks_seharusnya'].mean():.2f}")
    print(f"  Sel  mean={subset['selisih_sks'].mean():.2f}")

spark.stop()

print()
print("=" * 100)
print("AUDIT SELESAI")
print("=" * 100)
