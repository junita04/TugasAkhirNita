import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd
import numpy as np
from backend.spark.session import get_spark

spark = get_spark('FullAudit2')

print("=" * 100)
print("COMPREHENSIVE ML PIPELINE AUDIT - CORRECTED")
print("=" * 100)

# ============================================================
# 1. AUDIT INFERENCE DATA FROM FEATURE STORE
# ============================================================
print()
print("=" * 100)
print("1. AUDIT DATA INFERENCE PER ANGKATAN (DARI FEATURE STORE)")
print("=" * 100)

inference_fs = spark.table('iceberg.feature_store.inference_dataset').toPandas()
print(f"Total inference: {len(inference_fs)}")

FEATURES = ['jk_enc', 'angkatan', 'ip', 'ipk', 'total_sks', 'jumlah_mk', 'sks_seharusnya', 'selisih_sks']

print()
print("FEATURE STATS PER ANGKATAN (INFERENCE):")
print()
header = f"{'Angkatan':<10} {'N':>6} {'Mean SKS':>10} {'Med SKS':>9} {'Min SKS':>9} {'Max SKS':>9} {'Mean IPK':>10} {'Mean Sem':>9} {'Mean SKS_S':>11} {'Mean Selisih':>13}"
print(header)
print("-" * len(header))

for ang in [2022, 2023, 2024]:
    subset = inference_fs[inference_fs['angkatan'] == ang]
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
print("SEMESTER DISTRIBUTION:")
for ang in [2022, 2023, 2024]:
    subset = inference_fs[inference_fs['angkatan'] == ang]
    sem_dist = subset['semester'].value_counts().sort_index()
    print(f"  Angkatan {ang}: {dict(sem_dist)}")

print()
print("SKS_SEHARUSNYA DISTRIBUTION:")
for ang in [2022, 2023, 2024]:
    subset = inference_fs[inference_fs['angkatan'] == ang]
    sks_dist = subset['sks_seharusnya'].value_counts().sort_index()
    print(f"  Angkatan {ang}: {dict(sks_dist)}")

# ============================================================
# 2. AUDIT PROBABILITY DISTRIBUTION
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
# 3. FEATURE DISTRIBUTION TRAINING vs INFERENCE
# ============================================================
print()
print("=" * 100)
print("3. FEATURE DISTRIBUTION: TRAINING vs INFERENCE")
print("=" * 100)

training_fs = spark.table('iceberg.feature_store.training_dataset').toPandas()

print()
header = f"{'Feature':<16} {'Set':<16} {'Min':>10} {'Max':>10} {'Mean':>10} {'Median':>10} {'Std':>10}"
print(header)
print("-" * len(header))

for feat in FEATURES:
    t = training_fs[feat]
    print(f"{feat:<16} {'Training':<16} {t.min():>10.4f} {t.max():>10.4f} {t.mean():>10.4f} {t.median():>10.4f} {t.std():>10.4f}")
    
    for ang in [2022, 2023, 2024]:
        subset = inference_fs[inference_fs['angkatan'] == ang]
        s = subset[feat]
        print(f"{'':<16} {f'Infer {ang}':<16} {s.min():>10.4f} {s.max():>10.4f} {s.mean():>10.4f} {s.median():>10.4f} {s.std():>10.4f}")
    print()

# ============================================================
# 4. SELISIH SKS DISTRIBUTION
# ============================================================
print()
print("=" * 100)
print("4. SELISIH SKS DISTRIBUTION")
print("=" * 100)

print()
header = f"{'Angkatan':<10} {'N':>6} {'Sel<0':>8} {'Sel=0':>8} {'Sel>0':>8} {'%Sel<0':>8}"
print(header)
print("-" * 50)

for ang in [2022, 2023, 2024]:
    subset = inference_fs[inference_fs['angkatan'] == ang]
    n = len(subset)
    sel_neg = (subset['selisih_sks'] < 0).sum()
    sel_zero = (subset['selisih_sks'] == 0).sum()
    sel_pos = (subset['selisih_sks'] > 0).sum()
    pct_neg = sel_neg / n * 100 if n > 0 else 0
    print(f"{ang:<10} {n:>6} {sel_neg:>8} {sel_zero:>8} {sel_pos:>8} {pct_neg:>7.2f}%")

# Contoh
print()
print("TOP 10 Angkatan 2023 - Selisih SKS Terbesar:")
subset_2023 = inference_fs[inference_fs['angkatan'] == 2023].copy()
top10 = subset_2023.nlargest(10, 'selisih_sks')
print(top10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip']].to_string(index=False))

print()
print("TOP 10 Angkatan 2023 - Selisih SKS Terkecil:")
bottom10 = subset_2023.nsmallest(10, 'selisih_sks')
print(bottom10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip']].to_string(index=False))

print()
print("TOP 10 Angkatan 2024 - Selisih SKS Terbesar:")
subset_2024 = inference_fs[inference_fs['angkatan'] == 2024].copy()
top10 = subset_2024.nlargest(10, 'selisih_sks')
print(top10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip']].to_string(index=False))

print()
print("TOP 10 Angkatan 2024 - Selisih SKS Terkecil:")
bottom10 = subset_2024.nsmallest(10, 'selisih_sks')
print(bottom10[['id_mahasiswa', 'total_sks', 'sks_seharusnya', 'selisih_sks', 'ipk', 'ip']].to_string(index=False))

# ============================================================
# 5. TRAINING DATA COMPOSITION
# ============================================================
print()
print("=" * 100)
print("5. TRAINING DATA COMPOSITION")
print("=" * 100)

gold = spark.table('iceberg.gold.dim_mahasiswa').toPandas()
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

# Cek overlap
print()
inference_ids = set(inference_fs['id_mahasiswa'].values)
training_ids = set(training_fs['id_mahasiswa'].values)
overlap = inference_ids & training_ids
print(f"Inference IDs: {len(inference_ids)}")
print(f"Training IDs: {len(training_ids)}")
print(f"Overlap: {len(overlap)}")
if len(overlap) > 0:
    print(f"WARNING: {len(overlap)} overlap!")
else:
    print("PASS: No overlap")

# ============================================================
# 6. DIAGNOSIS: WHY 0 TW FOR 2023/2024
# ============================================================
print()
print("=" * 100)
print("6. DIAGNOSIS: ROOT CAUSE ANALYSIS")
print("=" * 100)

print()
print("TRAINING LABEL DISTRIBUTION:")
training_tw = training_fs[training_fs['label'] == 0]
training_tl = training_fs[training_fs['label'] == 1]
print(f"  Tepat Waktu (0): {len(training_tw)}")
print(f"  Terlambat (1): {len(training_tl)}")

print()
print("TRAINING FEATURE STATS BY LABEL:")
print()
header = f"{'Feature':<16} {'TW Mean':>10} {'TW Std':>10} {'TL Mean':>10} {'TL Std':>10}"
print(header)
print("-" * 56)
for feat in FEATURES:
    tw_mean = training_tw[feat].mean()
    tw_std = training_tw[feat].std()
    tl_mean = training_tl[feat].mean()
    tl_std = training_tl[feat].std()
    print(f"{feat:<16} {tw_mean:>10.4f} {tw_std:>10.4f} {tl_mean:>10.4f} {tl_std:>10.4f}")

print()
print("WHY 2023/2024 = 0 TEWAT Waktu:")
print()
print("CRITICAL FINDING:")
print("  Angkatan 2023: semester=5, sks_seharusnya=95")
print("  Angkatan 2024: semester=3, sks_seharusnya=55")
print()
print("  Inference 2023 stats:")
inf_2023 = inference_fs[inference_fs['angkatan'] == 2023]
print(f"    Total SKS mean: {inf_2023['total_sks'].mean():.2f}")
print(f"    SKS Seharusnya: 95")
print(f"    Selisih SKS mean: {inf_2023['selisih_sks'].mean():.2f}")
print(f"    IPK mean: {inf_2023['ipk'].mean():.4f}")
print()
print("  Inference 2024 stats:")
inf_2024 = inference_fs[inference_fs['angkatan'] == 2024]
print(f"    Total SKS mean: {inf_2024['total_sks'].mean():.2f}")
print(f"    SKS Seharusnya: 55")
print(f"    Selisih SKS mean: {inf_2024['selisih_sks'].mean():.2f}")
print(f"    IPK mean: {inf_2024['ipk'].mean():.4f}")

print()
print("PROBABILITY ANALYSIS:")
for ang in [2022, 2023, 2024]:
    subset = pred_no[pred_no['angkatan'] == ang]
    print(f"  Angkatan {ang}:")
    print(f"    P(TW) max: {subset['probability_tepat_waktu'].max():.6f}")
    print(f"    P(TW) mean: {subset['probability_tepat_waktu'].mean():.6f}")
    above_01 = (subset['probability_tepat_waktu'] > 0.1).sum()
    above_001 = (subset['probability_tepat_waktu'] > 0.01).sum()
    print(f"    P(TW) > 0.1: {above_01}")
    print(f"    P(TW) > 0.01: {above_001}")

spark.stop()

print()
print("=" * 100)
print("AUDIT SELESAI")
print("=" * 100)
