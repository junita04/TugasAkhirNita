"""
Gaussian Naive Bayes — Training Pipeline
Prediksi Tingkat Kelulusan Mahasiswa

HANYA GaussianNB. Tidak ada model lain.
"""

import sys
import os
import json
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

print("=" * 70)
print("GAUSSIAN NAIVE BAYES — TRAINING PIPELINE")
print("Prediksi Tingkat Kelulusan Mahasiswa")
print("Institut Teknologi Sumatera")
print("=" * 70)

# ============================================================
# STEP 1: LOAD DATA
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: LOAD DATA")
print("=" * 70)

spark = (
    SparkSession.builder
    .appName("TA_GaussianNB_Training")
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

spark.sparkContext.setLogLevel("ERROR")
print(f"Application ID: {spark.sparkContext.applicationId}")

fs_table = "iceberg.feature_store.feature_store_graduation_prediction"
df_spark = spark.table(fs_table)
total_rows = df_spark.count()
print(f"Feature Store: {fs_table}")
print(f"Total rows: {total_rows}")

print("\nSchema:")
df_spark.printSchema()

print("\nNULL checks:")
for col_name in df_spark.columns:
    null_cnt = df_spark.filter(F.col(col_name).isNull()).count()
    print(f"  {col_name}: {null_cnt} NULLs")

print("\nDuplicate id_mhs:")
dup_cnt = df_spark.groupBy("id_mhs").count().filter("count > 1").count()
print(f"  {dup_cnt} duplicates")

print("\nDistribusi status_kelulusan:")
df_spark.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).show()

print("Distribusi angkatan:")
df_spark.groupBy("angkatan").count().orderBy("angkatan").show(20, truncate=False)

# Convert to Pandas
pdf = df_spark.toPandas()
print(f"Pandas DataFrame shape: {pdf.shape}")

# ============================================================
# STEP 2: PREPROCESSING
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: PREPROCESSING")
print("=" * 70)

FEATURE_COLUMNS = [
    "jenis_kelamin",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "angkatan",
    "semester",
    "target_sks_kumulatif",
    "selisih_sks",
]
TARGET_COLUMN = "status_kelulusan"

X = pdf[FEATURE_COLUMNS].copy()
y_raw = pdf[TARGET_COLUMN].copy()

print(f"X shape: {X.shape}")
print(f"y shape: {y_raw.shape}")

# Encode target: Tepat Waktu=0, Terlambat=1
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y_raw)
label_mapping = dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))
print(f"\nTarget encoding: {label_mapping}")
print(f"Class 0 (Tepat Waktu): {np.sum(y == 0)}")
print(f"Class 1 (Terlambat):   {np.sum(y == 1)}")

# Feature types
categorical_features = ["jenis_kelamin"]
numerical_features = [c for c in FEATURE_COLUMNS if c not in categorical_features]

print(f"\nCategorical features: {categorical_features}")
print(f"Numerical features:   {numerical_features}")

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_features),
        ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features),
    ]
)

print("\nPreprocessing:")
print("  StandardScaler for numerical features")
print("  OneHotEncoder(drop='first') for categorical features")

# ============================================================
# STEP 3 & 4: GAUSSIAN NAIVE BAYES + 10-FOLD CROSS VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 3 & 4: GAUSSIAN NAIVE BAYES + 10-FOLD CROSS VALIDATION")
print("=" * 70)

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

fold_results = []
fold_confusion_matrices = []

print("\nFold-by-Fold Results:")
print("-" * 80)
print(f"{'Fold':<6} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("-" * 80)

for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y), 1):
    X_train_fold = X.iloc[train_idx]
    X_val_fold = X.iloc[val_idx]
    y_train_fold = y[train_idx]
    y_val_fold = y[val_idx]

    # Create pipeline: preprocess + GaussianNB
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", GaussianNB()),
    ])

    # FIT on training fold only
    pipeline.fit(X_train_fold, y_train_fold)

    # Predict on validation fold
    y_pred_fold = pipeline.predict(X_val_fold)

    # Calculate metrics
    acc = accuracy_score(y_val_fold, y_pred_fold)
    prec = precision_score(y_val_fold, y_pred_fold, average="weighted", zero_division=0)
    rec = recall_score(y_val_fold, y_pred_fold, average="weighted", zero_division=0)
    f1 = f1_score(y_val_fold, y_pred_fold, average="weighted", zero_division=0)
    cm = confusion_matrix(y_val_fold, y_pred_fold)

    fold_results.append({
        "fold": fold_idx,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
    })
    fold_confusion_matrices.append(cm)

    print(f"Fold {fold_idx:<3} {acc:>10.4f} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f}")

print("-" * 80)

# Calculate mean and std
accuracies = [r["accuracy"] for r in fold_results]
precisions = [r["precision"] for r in fold_results]
recalls = [r["recall"] for r in fold_results]
f1_scores = [r["f1_score"] for r in fold_results]

mean_acc = np.mean(accuracies)
std_acc = np.std(accuracies)
mean_prec = np.mean(precisions)
std_prec = np.std(precisions)
mean_rec = np.mean(recalls)
std_rec = np.std(recalls)
mean_f1 = np.mean(f1_scores)
std_f1 = np.std(f1_scores)

print(f"\nMean ± Std Results (10-Fold Cross Validation):")
print(f"  Accuracy:    {mean_acc:.4f} ± {std_acc:.4f}")
print(f"  Precision:   {mean_prec:.4f} ± {std_prec:.4f}")
print(f"  Recall:      {mean_rec:.4f} ± {std_rec:.4f}")
print(f"  F1-Score:    {mean_f1:.4f} ± {std_f1:.4f}")

# Aggregate confusion matrix
agg_cm = np.sum(fold_confusion_matrices, axis=0)
print(f"\nAggregate Confusion Matrix (10-Fold):")
print(f"                 Predicted")
print(f"                 Tepat Waktu  Terlambat")
print(f"  Actual Tepat Waktu    {agg_cm[0][0]:>6}      {agg_cm[0][1]:>6}")
print(f"  Actual Terlambat      {agg_cm[1][0]:>6}      {agg_cm[1][1]:>6}")

# ============================================================
# STEP 5: EVALUATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: EVALUATION")
print("=" * 70)

# Use last fold's predictions for classification report detail
# But better: aggregate predictions from all folds
all_y_true = []
all_y_pred = []

for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y), 1):
    X_train_fold = X.iloc[train_idx]
    X_val_fold = X.iloc[val_idx]
    y_train_fold = y[train_idx]
    y_val_fold = y[val_idx]

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", GaussianNB()),
    ])
    pipeline.fit(X_train_fold, y_train_fold)
    y_pred_fold = pipeline.predict(X_val_fold)

    all_y_true.extend(y_val_fold)
    all_y_pred.extend(y_pred_fold)

all_y_true = np.array(all_y_true)
all_y_pred = np.array(all_y_pred)

print("\nClassification Report (All Folds Combined):")
target_names = label_encoder.classes_
cr = classification_report(all_y_true, all_y_pred, target_names=target_names)
print(cr)

print("Confusion Matrix (All Folds Combined):")
cm_final = confusion_matrix(all_y_true, all_y_pred)
print(f"                 Predicted")
print(f"                 Tepat Waktu  Terlambat")
print(f"  Actual Tepat Waktu    {cm_final[0][0]:>6}      {cm_final[0][1]:>6}")
print(f"  Actual Terlambat      {cm_final[1][0]:>6}      {cm_final[1][1]:>6}")

# ============================================================
# STEP 6: MODEL FINAL
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: MODEL FINAL (trained on all 13,347 samples)")
print("=" * 70)

final_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", GaussianNB()),
])

final_pipeline.fit(X, y)
print("Final GaussianNB trained on all data")
print(f"  Training samples: {len(X)}")

# Predictions on full dataset for reporting
y_pred_full = final_pipeline.predict(X)

# Save model
models_dir = "/opt/airflow/models/graduation_prediction_gnb"
os.makedirs(models_dir, exist_ok=True)

model_path = os.path.join(models_dir, "model_gnb.joblib")
joblib.dump(final_pipeline, model_path, compress=0, protocol=2)
print(f"\nModel saved: {model_path}")

encoder_path = os.path.join(models_dir, "label_encoder.joblib")
joblib.dump(label_encoder, encoder_path, compress=0, protocol=2)
print(f"Encoder saved: {encoder_path}")

metadata = {
    "model_name": "Gaussian Naive Bayes",
    "features": FEATURE_COLUMNS,
    "target": TARGET_COLUMN,
    "target_encoding": {k: int(v) for k, v in label_mapping.items()},
    "preprocessing": {
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "scaler": "StandardScaler",
        "encoder": "OneHotEncoder(drop='first')",
    },
    "training_config": {
        "random_state": 42,
        "cv_folds": 10,
        "shuffle": True,
    },
    "cross_validation": {
        "mean_accuracy": float(mean_acc),
        "std_accuracy": float(std_acc),
        "mean_precision": float(mean_prec),
        "std_precision": float(std_prec),
        "mean_recall": float(mean_rec),
        "std_recall": float(std_rec),
        "mean_f1": float(mean_f1),
        "std_f1": float(std_f1),
    },
    "fold_results": [
        {
            "fold": r["fold"],
            "accuracy": float(r["accuracy"]),
            "precision": float(r["precision"]),
            "recall": float(r["recall"]),
            "f1_score": float(r["f1_score"]),
        }
        for r in fold_results
    ],
    "training_date": datetime.now().isoformat(),
    "total_samples": int(total_rows),
}

metadata_path = os.path.join(models_dir, "metadata.json")
with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2, default=str)
print(f"Metadata saved: {metadata_path}")

# ============================================================
# STEP 7: HASIL KELULUSAN PER ANGKATAN (AKTUAL)
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: HASIL KELULUSAN PER ANGKATAN (AKTUAL)")
print("=" * 70)

angkatan_data = pdf.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    tepat_waktu=("status_kelulusan", lambda x: (x == "Tepat Waktu").sum()),
    terlambat=("status_kelulusan", lambda x: (x == "Terlambat").sum()),
).reset_index()

angkatan_data["pct_tepat_waktu"] = (angkatan_data["tepat_waktu"] / angkatan_data["total"] * 100).round(2)
angkatan_data["pct_terlambat"] = (angkatan_data["terlambat"] / angkatan_data["total"] * 100).round(2)

print(f"\n{'Angkatan':<10} {'Total':>8} {'Tepat Waktu':>13} {'Terlambat':>11} {'% Tepat Waktu':>15} {'% Terlambat':>13}")
print("-" * 75)
for _, row in angkatan_data.iterrows():
    print(f"{int(row['angkatan']):<10} {int(row['total']):>8} {int(row['tepat_waktu']):>13} {int(row['terlambat']):>11} {row['pct_tepat_waktu']:>14.2f}% {row['pct_terlambat']:>12.2f}%")

total_all = angkatan_data["total"].sum()
total_tw = angkatan_data["tepat_waktu"].sum()
total_tl = angkatan_data["terlambat"].sum()
print("-" * 75)
print(f"{'TOTAL':<10} {int(total_all):>8} {int(total_tw):>13} {int(total_tl):>11} {total_tw/total_all*100:>14.2f}% {total_tl/total_all*100:>12.2f}%")

# Verify
print(f"\nVerifikasi: Tepat Waktu + Terlambat = Total Lulusan")
for _, row in angkatan_data.iterrows():
    check = int(row["tepat_waktu"]) + int(row["terlambat"])
    status = "OK" if check == int(row["total"]) else "MISMATCH"
    print(f"  Angkatan {int(row['angkatan'])}: {int(row['tepat_waktu'])} + {int(row['terlambat'])} = {check} (Total: {int(row['total'])}) [{status}]")

# ============================================================
# STEP 8: HASIL PREDIKSI PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 8: HASIL PREDIKSI MODEL PER ANGKATAN")
print("=" * 70)

# Add predictions to dataframe
pdf["prediksi"] = [label_encoder.classes_[p] for p in y_pred_full]

prediksi_angkatan = pdf.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    pred_tepat_waktu=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    pred_terlambat=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()

print(f"\n{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10}")
print("-" * 42)
for _, row in prediksi_angkatan.iterrows():
    print(f"{int(row['angkatan']):<10} {int(row['total']):>8} {int(row['pred_tepat_waktu']):>10} {int(row['pred_terlambat']):>10}")
print("-" * 42)
print(f"{'TOTAL':<10} {int(prediksi_angkatan['total'].sum()):>8} {int(prediksi_angkatan['pred_tepat_waktu'].sum()):>10} {int(prediksi_angkatan['pred_terlambat'].sum()):>10}")

# ============================================================
# STEP 8B: PERBANDINGAN AKTUAL vs PREDIKSI PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("PERBANDINGAN AKTUAL vs PREDIKSI PER ANGKATAN")
print("=" * 70)

comparison = pdf.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    aktual_tepat_waktu=("status_kelulusan", lambda x: (x == "Tepat Waktu").sum()),
    aktual_terlambat=("status_kelulusan", lambda x: (x == "Terlambat").sum()),
    pred_tepat_waktu=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    pred_terlambat=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()

comparison["diff_tepat_waktu"] = comparison["pred_tepat_waktu"] - comparison["aktual_tepat_waktu"]
comparison["diff_terlambat"] = comparison["pred_terlambat"] - comparison["aktual_terlambat"]

print(f"\n{'Angkatan':<10} {'Total':>6} {'Ak TW':>6} {'Pr TW':>6} {'Diff':>6} {'Ak TL':>6} {'Pr TL':>6} {'Diff':>6}")
print("-" * 62)
for _, row in comparison.iterrows():
    diff_tw = int(row["diff_tepat_waktu"])
    diff_tl = int(row["diff_terlambat"])
    sign_tw = "+" if diff_tw > 0 else ""
    sign_tl = "+" if diff_tl > 0 else ""
    print(f"{int(row['angkatan']):<10} {int(row['total']):>6} {int(row['aktual_tepat_waktu']):>6} {int(row['pred_tepat_waktu']):>6} {sign_tw}{diff_tw:>5} {int(row['aktual_terlambat']):>6} {int(row['pred_terlambat']):>6} {sign_tl}{diff_tl:>5}")

print("\nKeterangan:")
print("  Diff = Prediksi - Aktual")
print("  Positif (+) = Model memprediksi LEBIH BANYAK dari aktual")
print("  Negatif (-) = Model memprediksi LEBIH SEDIKIT dari aktual")

# ============================================================
# STEP 9: FINAL REPORT
# ============================================================
print("\n" + "=" * 70)
print("GAUSSIAN NAIVE BAYES — TRAINING REPORT")
print("=" * 70)

print(f"""
1. DATASET
   Source: {fs_table}

2. JUMLAH DATA
   Total: {total_rows} mahasiswa LULUS

3. FITUR (8 fitur)
   Categorical: {categorical_features}
   Numerical:   {numerical_features}

4. TARGET
   Column: {TARGET_COLUMN}
   Encoding: {label_mapping}

5. DISTRIBUSI TARGET
   Tepat Waktu: {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)
   Terlambat:   {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)

6. PREPROCESSING
   Numerical: StandardScaler
   Categorical: OneHotEncoder(drop='first')

7. METODE: Gaussian Naive Bayes (GaussianNB)

8. CROSS VALIDATION: Stratified K-Fold 10
   n_splits: 10
   shuffle: True
   random_state: 42

9. HASIL FOLD 1-10
""")

print(f"   {'Fold':<6} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("   " + "-" * 50)
for r in fold_results:
    print(f"   Fold {r['fold']:<3} {r['accuracy']:>10.4f} {r['precision']:>10.4f} {r['recall']:>10.4f} {r['f1_score']:>10.4f}")

print(f"""
10. Mean ± Std Accuracy:    {mean_acc:.4f} ± {std_acc:.4f}
11. Mean ± Std Precision:   {mean_prec:.4f} ± {std_prec:.4f}
12. Mean ± Std Recall:      {mean_rec:.4f} ± {std_rec:.4f}
13. Mean ± Std F1-Score:    {mean_f1:.4f} ± {std_f1:.4f}

14. CONFUSION MATRIX
""")

print(f"                 Predicted")
print(f"                 Tepat Waktu  Terlambat")
print(f"  Actual Tepat Waktu    {cm_final[0][0]:>6}      {cm_final[0][1]:>6}")
print(f"  Actual Terlambat      {cm_final[1][0]:>6}      {cm_final[1][1]:>6}")

print(f"""
15. CLASSIFICATION REPORT
{cr}
""")

print("=" * 70)
print("HASIL KELULUSAN PER ANGKATAN")
print("=" * 70)

print(f"\n{'Angkatan':<10} {'Total':>8} {'Tepat Waktu':>13} {'Terlambat':>11} {'% Tepat Waktu':>15} {'% Terlambat':>13}")
print("-" * 75)
for _, row in angkatan_data.iterrows():
    print(f"{int(row['angkatan']):<10} {int(row['total']):>8} {int(row['tepat_waktu']):>13} {int(row['terlambat']):>11} {row['pct_tepat_waktu']:>14.2f}% {row['pct_terlambat']:>12.2f}%")
print("-" * 75)
print(f"{'TOTAL':<10} {int(total_all):>8} {int(total_tw):>13} {int(total_tl):>11} {total_tw/total_all*100:>14.2f}% {total_tl/total_all*100:>12.2f}%")

print("\n" + "=" * 70)
print("HASIL PREDIKSI PER ANGKATAN")
print("=" * 70)

print(f"\n{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10}")
print("-" * 42)
for _, row in prediksi_angkatan.iterrows():
    print(f"{int(row['angkatan']):<10} {int(row['total']):>8} {int(row['pred_tepat_waktu']):>10} {int(row['pred_terlambat']):>10}")
print("-" * 42)
print(f"{'TOTAL':<10} {int(prediksi_angkatan['total'].sum()):>8} {int(prediksi_angkatan['pred_tepat_waktu'].sum()):>10} {int(prediksi_angkatan['pred_terlambat'].sum()):>10}")

print("\n" + "=" * 70)
print("PERBANDINGAN AKTUAL vs PREDIKSI")
print("=" * 70)

print(f"\n{'Angkatan':<10} {'Total':>6} {'Ak TW':>6} {'Pr TW':>6} {'Diff':>6} {'Ak TL':>6} {'Pr TL':>6} {'Diff':>6}")
print("-" * 62)
for _, row in comparison.iterrows():
    diff_tw = int(row["diff_tepat_waktu"])
    diff_tl = int(row["diff_terlambat"])
    sign_tw = "+" if diff_tw > 0 else ""
    sign_tl = "+" if diff_tl > 0 else ""
    print(f"{int(row['angkatan']):<10} {int(row['total']):>6} {int(row['aktual_tepat_waktu']):>6} {int(row['pred_tepat_waktu']):>6} {sign_tw}{diff_tw:>5} {int(row['aktual_terlambat']):>6} {int(row['pred_terlambat']):>6} {sign_tl}{diff_tl:>5}")

print(f"""
============================================================
STATUS
============================================================

GAUSSIAN NAIVE BAYES TRAINING SELESAI

Model: GaussianNB
CV F1-Score: {mean_f1:.4f} ± {std_f1:.4f}
CV Accuracy: {mean_acc:.4f} ± {std_acc:.4f}

Lokasi Model: {model_path}
Lokasi Metadata: {metadata_path}
============================================================
""")

spark.stop()
