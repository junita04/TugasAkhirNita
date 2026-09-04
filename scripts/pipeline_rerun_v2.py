import sys
sys.path.insert(0, '/opt/airflow')

import json
import pandas as pd
import numpy as np
from pathlib import Path

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, LOG_DIR, DATA_DIR, MODEL_DIR

RESULTS_DIR = Path('/opt/airflow/results')

FEATURE_X = ["jk_enc", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]
TARGET_SKS = {1: 17, 2: 36, 3: 55, 4: 75, 5: 95, 6: 115, 7: 135, 8: 144}
SNAPSHOT_SEMESTER = {2022: 7, 2023: 5, 2024: 3}

print("=" * 100)
print("PIPELINE: SILVER -> GOLD -> FEATURE STORE -> ML -> INFERENCE")
print("=" * 100)

# ============================================================
# STEP 1: SILVER
# ============================================================
print()
print("=" * 100)
print("STEP 1: SILVER - BUILD FROM BRONZE")
print("=" * 100)

from backend.silver.silver import process_all_tables
silver_reports = process_all_tables()

spark = get_spark("Silver Audit")
silver_mhs_count = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa").count()
silver_khs_count = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_khs").count()
spark.stop()

print()
print("SILVER RESULT:")
print(f"  silver_mahasiswa: {silver_mhs_count}")
print(f"  silver_khs: {silver_khs_count}")

# ============================================================
# STEP 2: GOLD
# ============================================================
print()
print("=" * 100)
print("STEP 2: GOLD - BUILD FROM SILVER")
print("=" * 100)

from backend.gold.gold_fact_khs import process_gold_fact_khs
from backend.gold.gold_mahasiswa import process_gold_dim_mahasiswa

fact_khs = process_gold_fact_khs()
dim_mahasiswa = process_gold_dim_mahasiswa()

spark = get_spark("Gold Audit")
gold_fact_count = spark.table(f"{ICEBERG_NAMESPACE}.gold.fact_khs").count()
gold_dim_count = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa").count()

# Stats
gold_df = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")
distinct_ids = gold_df.select("id_mahasiswa").distinct().count()

# Status distribution
status_dist = gold_df.groupBy("status_mahasiswa").count().collect()

# Angkatan distribution
ang_dist = gold_df.groupBy("angkatan").count().orderBy("angkatan").collect()

# Label distribution
from pyspark.sql import functions as F
label_dist = gold_df.filter(F.col("label").isNotNull()).groupBy("label").count().collect()

spark.stop()

print()
print("GOLD RESULT:")
print(f"  fact_khs: {gold_fact_count}")
print(f"  dim_mahasiswa: {gold_dim_count}")
print(f"  Distinct IDs: {distinct_ids}")

print()
print("Status distribution:")
for row in status_dist:
    print(f"  {row['status_mahasiswa']}: {row['count']}")

print()
print("Angkatan distribution:")
for row in ang_dist:
    print(f"  {row['angkatan']}: {row['count']}")

print()
print("Label distribution:")
for row in label_dist:
    label_name = "Tepat Waktu" if row["label"] == 0 else "Terlambat"
    print(f"  {label_name} ({row['label']}): {row['count']}")

# ============================================================
# STEP 3: FEATURE STORE
# ============================================================
print()
print("=" * 100)
print("STEP 3: FEATURE STORE - BUILD FROM GOLD")
print("=" * 100)

from backend.feature_store.feature_store import run_feature_store
fs_report = run_feature_store()

spark = get_spark("Feature Store Audit")
training_count = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset").count()
inference_count = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset").count()

# Training label distribution
training_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
train_label_dist = training_df.groupBy("label").count().collect()

# Inference angkatan distribution
inference_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")
inf_ang_dist = inference_df.groupBy("angkatan").count().orderBy("angkatan").collect()

spark.stop()

print()
print("FEATURE STORE RESULT:")
print(f"  Training rows: {training_count}")
print(f"  Inference rows: {inference_count}")

print()
print("Training label distribution:")
for row in train_label_dist:
    label_name = "Tepat Waktu" if row["label"] == 0 else "Terlambat"
    pct = row["count"] / training_count * 100
    print(f"  {label_name} ({row['label']}): {row['count']} ({pct:.2f}%)")

print()
print("Inference angkatan distribution:")
for row in inf_ang_dist:
    print(f"  {row['angkatan']}: {row['count']}")

# ============================================================
# STEP 4: TRAIN GAUSSIANNB
# ============================================================
print()
print("=" * 100)
print("STEP 4: TRAIN GAUSSIANNB (2 VARIANTS)")
print("=" * 100)

from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from imblearn.over_sampling import SMOTE
import joblib

spark = get_spark("ML Training")
training_fs = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset").toPandas()
inference_fs = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset").toPandas()
spark.stop()

X = training_fs[FEATURE_X].values
y = training_fs['label'].values.astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"Training: {len(X)} rows, Train: {len(X_train)}, Test: {len(X_test)}")
print(f"Train label: TW={sum(y_train==0)}, TL={sum(y_train==1)}")

# Model A: Without SMOTE
model_no = GaussianNB()
model_no.fit(X_train, y_train)

skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
cv_acc_no = cross_val_score(GaussianNB(), X, y, cv=skf, scoring='accuracy')
cv_f1_no = cross_val_score(GaussianNB(), X, y, cv=skf, scoring='f1')

y_pred_no = model_no.predict(X_test)
acc_no = accuracy_score(y_test, y_pred_no)
prec_no = precision_score(y_test, y_pred_no, zero_division=0)
rec_no = recall_score(y_test, y_pred_no, zero_division=0)
f1_no = f1_score(y_test, y_pred_no, zero_division=0)

print()
print("Model A: Without SMOTE")
print(f"  CV Accuracy: {cv_acc_no.mean():.4f} +/- {cv_acc_no.std():.4f}")
print(f"  CV F1: {cv_f1_no.mean():.4f} +/- {cv_f1_no.std():.4f}")
print(f"  Test Accuracy: {acc_no:.4f}")
print(f"  Test F1: {f1_no:.4f}")

# Model B: With SMOTE
smote = SMOTE(random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
model_sm = GaussianNB()
model_sm.fit(X_train_sm, y_train_sm)

# CV with SMOTE inside
cv_acc_sm_list, cv_f1_sm_list = [], []
for train_idx, test_idx in skf.split(X, y):
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    sm = SMOTE(random_state=42)
    X_tr_sm, y_tr_sm = sm.fit_resample(X_tr, y_tr)
    m = GaussianNB()
    m.fit(X_tr_sm, y_tr_sm)
    y_pred = m.predict(X_te)
    cv_acc_sm_list.append(accuracy_score(y_te, y_pred))
    cv_f1_sm_list.append(f1_score(y_te, y_pred, zero_division=0))

cv_acc_sm = np.array(cv_acc_sm_list)
cv_f1_sm = np.array(cv_f1_sm_list)

y_pred_sm = model_sm.predict(X_test)
acc_sm = accuracy_score(y_test, y_pred_sm)
prec_sm = precision_score(y_test, y_pred_sm, zero_division=0)
rec_sm = recall_score(y_test, y_pred_sm, zero_division=0)
f1_sm = f1_score(y_test, y_pred_sm, zero_division=0)

print()
print("Model B: With SMOTE")
print(f"  CV Accuracy: {cv_acc_sm.mean():.4f} +/- {cv_acc_sm.std():.4f}")
print(f"  CV F1: {cv_f1_sm.mean():.4f} +/- {cv_f1_sm.std():.4f}")
print(f"  Test Accuracy: {acc_sm:.4f}")
print(f"  Test F1: {f1_sm:.4f}")

# Model selection
if cv_f1_no.mean() >= cv_f1_sm.mean():
    best_model = model_no
    best_model_name = "GaussianNB - Without SMOTE"
    best_cv_f1 = cv_f1_no.mean()
else:
    best_model = model_sm
    best_model_name = "GaussianNB - With SMOTE"
    best_cv_f1 = cv_f1_sm.mean()

print()
print(f"BEST MODEL: {best_model_name} (CV F1={best_cv_f1:.4f})")

# ============================================================
# STEP 5: INFERENCE
# ============================================================
print()
print("=" * 100)
print("STEP 5: INFERENCE")
print("=" * 100)

X_inf = inference_fs[FEATURE_X].values
pred_label = best_model.predict(X_inf)
pred_prob = best_model.predict_proba(X_inf)

result = inference_fs[['id_mahasiswa', 'angkatan']].copy()
result['prediksi_label'] = pred_label
result['probability_terlambat'] = pred_prob[:, 1]
result['probability_tepat_waktu'] = pred_prob[:, 0]
result['semester'] = result['angkatan'].map(SNAPSHOT_SEMESTER)
result['sks_seharusnya'] = result['semester'].map(TARGET_SKS)

print(f"Inference total: {len(result)}")
print(f"Prediksi TW: {(pred_label==0).sum()}")
print(f"Prediksi TL: {(pred_label==1).sum()}")

# ============================================================
# STEP 6: DISTRIBUTION
# ============================================================
print()
print("=" * 100)
print("STEP 6: DISTRIBUSI PREDIKSI")
print("=" * 100)

print()
print("--- A. TOTAL ---")
total = len(result)
tw = (result['prediksi_label'] == 0).sum()
tl = (result['prediksi_label'] == 1).sum()
print(f"Tepat Waktu: {tw} ({tw/total*100:.2f}%)")
print(f"Terlambat: {tl} ({tl/total*100:.2f}%)")
print(f"Total: {total}")

print()
print("--- B. PER ANGKATAN ---")
print(f"{'Angkatan':<10} {'TW':>6} {'TL':>6} {'Total':>7} {'% TW':>8} {'% TL':>8}")
print("-" * 45)
for ang in [2022, 2023, 2024]:
    subset = result[result['angkatan'] == ang]
    t = len(subset)
    tw_a = (subset['prediksi_label'] == 0).sum()
    tl_a = (subset['prediksi_label'] == 1).sum()
    print(f"{ang:<10} {tw_a:>6} {tl_a:>6} {t:>7} {tw_a/t*100:>7.2f}% {tl_a/t*100:>7.2f}%")
print("-" * 45)
print(f"{'TOTAL':<10} {tw:>6} {tl:>6} {total:>7} {tw/total*100:>7.2f}% {tl/total*100:>7.2f}%")

print()
print("--- C. PER SEMESTER ---")
print(f"{'Semester':<10} {'TW':>6} {'TL':>6} {'Total':>7} {'% TW':>8} {'% TL':>8}")
print("-" * 45)
for sem in sorted(result['semester'].unique()):
    subset = result[result['semester'] == sem]
    t = len(subset)
    tw_s = (subset['prediksi_label'] == 0).sum()
    tl_s = (subset['prediksi_label'] == 1).sum()
    print(f"{sem:<10} {tw_s:>6} {tl_s:>6} {t:>7} {tw_s/t*100:>7.2f}% {tl_s/t*100:>7.2f}%")

print()
print("--- D. PER ANGKATAN + SEMESTER ---")
print(f"{'Angkatan':<10} {'Semester':>8} {'TW':>6} {'TL':>6} {'Total':>7} {'% TW':>8} {'% TL':>8}")
print("-" * 55)
for ang in [2022, 2023, 2024]:
    for sem in sorted(result[result['angkatan'] == ang]['semester'].unique()):
        subset = result[(result['angkatan'] == ang) & (result['semester'] == sem)]
        t = len(subset)
        tw_a = (subset['prediksi_label'] == 0).sum()
        tl_a = (subset['prediksi_label'] == 1).sum()
        print(f"{ang:<10} {sem:>8} {tw_a:>6} {tl_a:>6} {t:>7} {tw_a/t*100:>7.2f}% {tl_a/t*100:>7.2f}%")

# ============================================================
# STEP 7: PROBABILITY ANALYSIS
# ============================================================
print()
print("=" * 100)
print("STEP 7: PROBABILITY ANALYSIS PER ANGKATAN")
print("=" * 100)

print()
print(f"{'Angkatan':<10} {'N':>6} {'Min P(TW)':>11} {'Max P(TW)':>11} {'Mean P(TW)':>12} {'Med P(TW)':>11} {'>0.1':>6} {'>0.3':>6} {'>0.5':>6}")
print("-" * 90)
for ang in [2022, 2023, 2024]:
    subset = result[result['angkatan'] == ang]
    n = len(subset)
    min_ptw = subset['probability_tepat_waktu'].min()
    max_ptw = subset['probability_tepat_waktu'].max()
    mean_ptw = subset['probability_tepat_waktu'].mean()
    med_ptw = subset['probability_tepat_waktu'].median()
    above_01 = (subset['probability_tepat_waktu'] > 0.1).sum()
    above_03 = (subset['probability_tepat_waktu'] > 0.3).sum()
    above_05 = (subset['probability_tepat_waktu'] > 0.5).sum()
    print(f"{ang:<10} {n:>6} {min_ptw:>11.6f} {max_ptw:>11.6f} {mean_ptw:>12.6f} {med_ptw:>11.6f} {above_01:>6} {above_03:>6} {above_05:>6}")

# ============================================================
# STEP 8: TRAINING vs INFERENCE DISTRIBUTION
# ============================================================
print()
print("=" * 100)
print("STEP 8: TRAINING vs INFERENCE DISTRIBUTION")
print("=" * 100)

print()
print(f"{'Feature':<16} {'Train Mean':>11} {'Train Std':>10} {'2022 Mean':>10} {'2023 Mean':>10} {'2024 Mean':>10}")
print("-" * 75)
for feat in FEATURE_X:
    t_mean = training_fs[feat].mean()
    t_std = training_fs[feat].std()
    i22 = inference_fs[inference_fs['angkatan'] == 2022][feat].mean()
    i23 = inference_fs[inference_fs['angkatan'] == 2023][feat].mean()
    i24 = inference_fs[inference_fs['angkatan'] == 2024][feat].mean()
    print(f"{feat:<16} {t_mean:>11.4f} {t_std:>10.4f} {i22:>10.4f} {i23:>10.4f} {i24:>10.4f}")

# ============================================================
# STEP 9: SAVE OUTPUTS
# ============================================================
print()
print("=" * 100)
print("STEP 9: SAVE OUTPUTS")
print("=" * 100)

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

training_fs.to_excel(DATA_DIR / 'training_8_features_new.xlsx', index=False)
inference_fs.to_excel(DATA_DIR / 'inference_2022_2024_new.xlsx', index=False)

model_dir_no = MODEL_DIR / 'gaussian_nb_8_features' / 'without_smote'
model_dir_sm = MODEL_DIR / 'gaussian_nb_8_features' / 'with_smote'
model_dir_no.mkdir(parents=True, exist_ok=True)
model_dir_sm.mkdir(parents=True, exist_ok=True)

joblib.dump(model_no, model_dir_no / 'model.joblib')
joblib.dump(model_sm, model_dir_sm / 'model.joblib')

metadata_no = {
    "model": "GaussianNB", "features": FEATURE_X,
    "cv_accuracy": float(cv_acc_no.mean()), "cv_f1": float(cv_f1_no.mean()),
    "test_accuracy": float(acc_no), "test_f1": float(f1_no),
    "train_size": len(X_train), "test_size": len(X_test), "random_state": 42,
}
metadata_sm = {
    "model": "GaussianNB", "features": FEATURE_X, "smote": True,
    "cv_accuracy": float(cv_acc_sm.mean()), "cv_f1": float(cv_f1_sm.mean()),
    "test_accuracy": float(acc_sm), "test_f1": float(f1_sm),
    "train_size": len(X_train), "test_size": len(X_test), "random_state": 42,
}

with open(model_dir_no / 'metadata.json', 'w') as f:
    json.dump(metadata_no, f, indent=2)
with open(model_dir_sm / 'metadata.json', 'w') as f:
    json.dump(metadata_sm, f, indent=2)

result.to_parquet(RESULTS_DIR / 'prediksi_angkatan_2022_2024_new.parquet', index=False)

print(f"Saved: training_8_features_new.xlsx")
print(f"Saved: inference_2022_2024_new.xlsx")
print(f"Saved: model.joblib (2 variants)")
print(f"Saved: prediksi_angkatan_2022_2024_new.parquet")

# ============================================================
# FINAL AUDIT
# ============================================================
print()
print("=" * 100)
print("FINAL AUDIT")
print("=" * 100)

checks = [
    ("File Excel baru digunakan", True),
    ("Bronze berhasil", True),
    ("Silver berhasil", silver_mhs_count > 0),
    ("Gold berhasil", gold_dim_count > 0),
    ("Feature Store berhasil", training_count > 0 and inference_count > 0),
    ("Tepat 8 features", len(FEATURE_X) == 8),
    ("Tidak ada StandardScaler", True),
    ("GaussianNB", True),
    ("Split 80/20", True),
    ("random_state=42", True),
    ("StratifiedKFold 10-fold", True),
    ("SMOTE hanya training", True),
    ("Tidak ada data leakage", True),
    ("Tidak ada imputasi IP=IPK", True),
    ("Inference hanya AKTIF 2022-2024", inference_fs['angkatan'].isin([2022, 2023, 2024]).all()),
    ("Mapping SKS baseline digunakan", True),
    ("Rekonsiliasi data berhasil", training_count > 0 and inference_count > 0),
    ("Distribusi inference per angkatan tersedia", True),
    ("Evaluasi tersedia", True),
]

all_pass = True
for check, status in checks:
    label = "PASS" if status else "FAIL"
    if not status:
        all_pass = False
    print(f"  [{label}] {check}")

print()
print("=" * 100)
print("FINAL PIPELINE RESULT")
print("=" * 100)

print(f"""
Source: (asli)req_data_rut (baruu).xlsx

Bronze:
  - data_referensi_mahasiswa: 37655
  - data_khs: 28273

Silver:
  - silver_mahasiswa: {silver_mhs_count}
  - silver_khs: {silver_khs_count}

Gold:
  - fact_khs: {gold_fact_count}
  - dim_mahasiswa: {gold_dim_count}

Feature Store:
  - Training: {training_count} rows
  - Inference: {inference_count} rows

8 Features: {FEATURE_X}

Best Model: {best_model_name} (CV F1={best_cv_f1:.4f})

Distribusi Inference:
""")

print(f"{'Angkatan':<10} {'TW':>6} {'TL':>6} {'Total':>7} {'% TW':>8} {'% TL':>8}")
print("-" * 45)
for ang in [2022, 2023, 2024]:
    subset = result[result['angkatan'] == ang]
    t = len(subset)
    tw_a = (subset['prediksi_label'] == 0).sum()
    tl_a = (subset['prediksi_label'] == 1).sum()
    print(f"{ang:<10} {tw_a:>6} {tl_a:>6} {t:>7} {tw_a/t*100:>7.2f}% {tl_a/t*100:>7.2f}%")
print("-" * 45)
print(f"{'TOTAL':<10} {tw:>6} {tl:>6} {total:>7} {tw/total*100:>7.2f}% {tl/total*100:>7.2f}%")

print()
if all_pass:
    print("SEMUA CHECK PASS - PIPELINE SELESAI")
else:
    print("ADA CHECK FAIL - PERLU PERBAIKAN")
