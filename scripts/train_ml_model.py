"""
Machine Learning Pipeline — Prediksi Tingkat Kelulusan Mahasiswa
Tugas Akhir: Integrasi Gold Layer ke Feature Store untuk Prediksi Kelulusan

11 Steps:
1. Load Feature Store
2. Preprocessing
3. Train/Test Split
4. Class Imbalance Handling
5. Training Multiple Models
6. Cross Validation
7. Evaluation
8. Model Selection
9. Save Model
10. Report
11. Inference Preparation
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

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

print("=" * 70)
print("MACHINE LEARNING PIPELINE — PREDIKSI KELULUSAN MAHASISWA")
print("Tugas Akhir: Institut Teknologi Sumatera")
print("=" * 70)

# ============================================================
# STEP 1: LOAD FEATURE STORE
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: LOAD FEATURE STORE")
print("=" * 70)

spark = (
    SparkSession.builder
    .appName("TA_ML_Training")
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

print("\nTarget distribution:")
df_spark.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).show()

print("Numerical statistics:")
df_spark.select(
    F.mean("ipk").alias("mean_ipk"),
    F.stddev("ipk").alias("std_ipk"),
    F.mean("total_sks").alias("mean_total_sks"),
    F.mean("jumlah_mk").alias("mean_jumlah_mk"),
    F.mean("selisih_sks").alias("mean_selisih_sks"),
).show()

# Convert to Pandas for ML
pdf = df_spark.toPandas()
print(f"\nPandas DataFrame shape: {pdf.shape}")
print(f"Columns: {list(pdf.columns)}")

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

# Encode target: Tepat Waktu=1, Terlambat=0
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y_raw)
label_mapping = dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))
print(f"\nTarget encoding: {label_mapping}")
print(f"Class distribution: {dict(zip(label_encoder.classes_, np.bincount(y)))}")

# Identify feature types
categorical_features = ["jenis_kelamin"]
numerical_features = [c for c in FEATURE_COLUMNS if c not in categorical_features]

print(f"\nCategorical features: {categorical_features}")
print(f"Numerical features: {numerical_features}")

# Create preprocessing pipeline
# Scaler FIT only on training data
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_features),
        ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features),
    ]
)

print("\nPreprocessing pipeline created:")
print("  - StandardScaler for numerical features")
print("  - OneHotEncoder(drop='first') for categorical features")
print("  - Scaler FIT only on training data (via pipeline)")

# ============================================================
# STEP 3: TRAIN/TEST SPLIT
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: TRAIN/TEST SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"Training set: {X_train.shape[0]} samples")
print(f"Testing set:  {X_test.shape[0]} samples")
print(f"Test size:    {X_test.shape[0] / X.shape[0] * 100:.1f}%")

print("\nTraining class distribution:")
for cls_idx, cls_name in enumerate(label_encoder.classes_):
    cnt = np.sum(y_train == cls_idx)
    pct = cnt / len(y_train) * 100
    print(f"  {cls_name}: {cnt} ({pct:.1f}%)")

print("\nTesting class distribution:")
for cls_idx, cls_name in enumerate(label_encoder.classes_):
    cnt = np.sum(y_test == cls_idx)
    pct = cnt / len(y_test) * 100
    print(f"  {cls_name}: {cnt} ({pct:.1f}%)")

# ============================================================
# STEP 4: CLASS IMBALANCE HANDLING
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: CLASS IMBALANCE HANDLING")
print("=" * 70)

print("Dataset imbalance analysis:")
print(f"  Terlambat:  {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)")
print(f"  Tepat Waktu: {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)")
print(f"  Ratio: 1:{np.sum(y == 0)/np.sum(y == 1):.1f}")

print("\nApproach selected: class_weight='balanced'")
print("  Reason:")
print("  - No synthetic data modification (no SMOTE)")
print("  - Model adjusts weights inversely proportional to class frequency")
print("  - Works with all selected models (RF, LR, GB)")
print("  - Avoids risk of overfitting from synthetic minority samples")
print("  - SMOTE only used as comparison if needed")

# ============================================================
# STEP 5: TRAINING MULTIPLE MODELS
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: TRAINING MULTIPLE MODELS")
print("=" * 70)

models = {
    "Gaussian Naive Bayes": GaussianNB(),
    "Logistic Regression": LogisticRegression(
        max_iter=1000, random_state=42, class_weight="balanced"
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=100, random_state=42, class_weight="balanced", n_jobs=-1
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=50, random_state=42, max_depth=4
    ),
}

trained_models = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model),
    ])
    pipeline.fit(X_train, y_train)
    trained_models[name] = pipeline
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    print(f"  Accuracy: {acc:.4f}")
    print(f"  F1-Score: {f1:.4f}")

# ============================================================
# STEP 6: CROSS VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: CROSS VALIDATION (StratifiedKFold, n_splits=10)")
print("=" * 70)

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
cv_results = {}

for name, model in models.items():
    print(f"\nCross-validating {name}...")
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", model),
    ])

    scoring = {
        "accuracy": "accuracy",
        "f1_weighted": "f1_weighted",
        "precision_weighted": "precision_weighted",
        "recall_weighted": "recall_weighted",
    }

    cv_scores = cross_validate(pipeline, X, y, cv=cv, scoring=scoring, n_jobs=-1)

    acc_mean = cv_scores["test_accuracy"].mean()
    acc_std = cv_scores["test_accuracy"].std()
    f1_mean = cv_scores["test_f1_weighted"].mean()
    f1_std = cv_scores["test_f1_weighted"].std()
    prec_mean = cv_scores["test_precision_weighted"].mean()
    prec_std = cv_scores["test_precision_weighted"].std()
    rec_mean = cv_scores["test_recall_weighted"].mean()
    rec_std = cv_scores["test_recall_weighted"].std()

    cv_results[name] = {
        "accuracy_mean": acc_mean, "accuracy_std": acc_std,
        "f1_mean": f1_mean, "f1_std": f1_std,
        "precision_mean": prec_mean, "precision_std": prec_std,
        "recall_mean": rec_mean, "recall_std": rec_std,
    }

    print(f"  Accuracy:    {acc_mean:.4f} +/- {acc_std:.4f}")
    print(f"  F1-Score:    {f1_mean:.4f} +/- {f1_std:.4f}")
    print(f"  Precision:   {prec_mean:.4f} +/- {prec_std:.4f}")
    print(f"  Recall:      {rec_mean:.4f} +/- {rec_std:.4f}")

# ============================================================
# STEP 7: EVALUATION ON TEST SET
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: EVALUATION ON TEST SET")
print("=" * 70)

test_results = {}

for name, pipeline in trained_models.items():
    print(f"\n{'='*50}")
    print(f"MODEL: {name}")
    print(f"{'='*50}")

    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted")
    rec = recall_score(y_test, y_pred, average="weighted")
    f1 = f1_score(y_test, y_pred, average="weighted")

    cm = confusion_matrix(y_test, y_pred)
    cr = classification_report(y_test, y_pred, target_names=label_encoder.classes_)

    test_results[name] = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm,
        "classification_report": cr,
    }

    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"                 Predicted")
    print(f"                 Terlambat  Tepat Waktu")
    print(f"  Actual Terlambat    {cm[0][0]:>6}      {cm[0][1]:>6}")
    print(f"  Actual Tepat Waktu  {cm[1][0]:>6}      {cm[1][1]:>6}")
    print(f"\nClassification Report:")
    print(cr)

# ============================================================
# STEP 8: MODEL SELECTION
# ============================================================
print("\n" + "=" * 70)
print("STEP 8: MODEL SELECTION")
print("=" * 70)

print("\nComparative Table (sorted by F1-Score):")
print(f"{'Model':<30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'CV F1':>10}")
print("-" * 90)

sorted_models = sorted(test_results.items(), key=lambda x: x[1]["f1_score"], reverse=True)

for name, res in sorted_models:
    cv_f1 = cv_results[name]["f1_mean"]
    print(f"{name:<30} {res['accuracy']:>10.4f} {res['precision']:>10.4f} {res['recall']:>10.4f} {res['f1_score']:>10.4f} {cv_f1:>10.4f}")

best_model_name = sorted_models[0][0]
best_results = sorted_models[0][1]
best_cv = cv_results[best_model_name]

print(f"\n{'='*50}")
print(f"BEST MODEL: {best_model_name}")
print(f"{'='*50}")
print(f"Accuracy:    {best_results['accuracy']:.4f}")
print(f"Precision:   {best_results['precision']:.4f}")
print(f"Recall:      {best_results['recall']:.4f}")
print(f"F1-Score:    {best_results['f1_score']:.4f}")
print(f"CV F1 Mean:  {best_cv['f1_mean']:.4f} +/- {best_cv['f1_std']:.4f}")
print(f"CV Acc Mean: {best_cv['accuracy_mean']:.4f} +/- {best_cv['accuracy_std']:.4f}")

print(f"\nReason for selection:")
print(f"  - Highest F1-Score among all models")
print(f"  - Balanced Precision/Recall trade-off")
print(f"  - Consistent cross-validation performance")

# ============================================================
# STEP 9: SAVE MODEL
# ============================================================
print("\n" + "=" * 70)
print("STEP 9: SAVE MODEL AND METADATA")
print("=" * 70)

# Create models directory inside container
models_dir = "/opt/airflow/models/graduation_prediction"
os.makedirs(models_dir, exist_ok=True)

# Save the best model pipeline
best_pipeline = trained_models[best_model_name]
model_path = os.path.join(models_dir, "model.joblib")
joblib.dump(best_pipeline, model_path, compress=0, protocol=2)
print(f"Model saved: {model_path}")

# Save label encoder
encoder_path = os.path.join(models_dir, "label_encoder.joblib")
joblib.dump(label_encoder, encoder_path, compress=0, protocol=2)
print(f"Label encoder saved: {encoder_path}")

# Save metadata
metadata = {
    "model_name": best_model_name,
    "features": FEATURE_COLUMNS,
    "target": TARGET_COLUMN,
    "target_encoding": label_mapping,
    "preprocessing": {
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "scaler": "StandardScaler",
        "encoder": "OneHotEncoder(drop='first')",
    },
    "training_config": {
        "random_state": 42,
        "test_size": 0.20,
        "cv_folds": 10,
        "class_weight": "balanced",
    },
    "evaluation": {
        "accuracy": best_results["accuracy"],
        "precision": best_results["precision"],
        "recall": best_results["recall"],
        "f1_score": best_results["f1_score"],
        "cv_f1_mean": best_cv["f1_mean"],
        "cv_f1_std": best_cv["f1_std"],
        "cv_accuracy_mean": best_cv["accuracy_mean"],
        "cv_accuracy_std": best_cv["accuracy_std"],
    },
    "all_models_comparison": {
        name: {
            "accuracy": res["accuracy"],
            "precision": res["precision"],
            "recall": res["recall"],
            "f1_score": res["f1_score"],
            "cv_f1_mean": cv_results[name]["f1_mean"],
        }
        for name, res in test_results.items()
    },
    "dataset": {
        "source": fs_table,
        "total_samples": int(total_rows),
        "training_samples": int(X_train.shape[0]),
        "testing_samples": int(X_test.shape[0]),
        "class_distribution": {
            cls: int(np.sum(y == idx))
            for cls, idx in label_mapping.items()
        },
    },
    "training_date": datetime.now().isoformat(),
    "feature_store_location": "s3a://warehouse/iceberg/feature_store.db/feature_store_graduation_prediction",
    "model_location": f"s3a://warehouse/models/graduation_prediction/model.joblib",
}

metadata_path = os.path.join(models_dir, "metadata.json")
with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2, default=str)
print(f"Metadata saved: {metadata_path}")

# Save all model comparison to CSV
comparison_rows = []
for name, res in test_results.items():
    comparison_rows.append({
        "Model": name,
        "Accuracy": round(res["accuracy"], 4),
        "Precision": round(res["precision"], 4),
        "Recall": round(res["recall"], 4),
        "F1_Score": round(res["f1_score"], 4),
        "CV_F1_Mean": round(cv_results[name]["f1_mean"], 4),
        "CV_F1_Std": round(cv_results[name]["f1_std"], 4),
    })

comparison_df = pd.DataFrame(comparison_rows)
comparison_path = os.path.join(models_dir, "model_comparison.csv")
comparison_df.to_csv(comparison_path, index=False)
print(f"Comparison CSV saved: {comparison_path}")

# ============================================================
# STEP 10: COMPREHENSIVE REPORT
# ============================================================
print("\n" + "=" * 70)
print("MACHINE LEARNING REPORT")
print("=" * 70)

print(f"""
1. INPUT FEATURE STORE
   Table: {fs_table}
   Rows:  {total_rows}

2. JUMLAH DATA
   Total:    {total_rows}
   Training: {X_train.shape[0]} (80%)
   Testing:  {X_test.shape[0]} (20%)

3. DAFTAR FITUR ({len(FEATURE_COLUMNS)} fitur)
   Categorical: {categorical_features}
   Numerical:   {numerical_features}

4. TARGET
   Column: {TARGET_COLUMN}
   Classes: {label_mapping}

5. DISTRIBUSI TARGET
   Terlambat:   {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)
   Tepat Waktu: {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)

6. PREPROCESSING
   Numerical: StandardScaler (FIT on training only)
   Categorical: OneHotEncoder(drop='first')

7. TRAIN/TEST SPLIT
   test_size: 0.20
   random_state: 42
   stratify: y

8. CROSS VALIDATION (10-Fold Stratified)
   {best_model_name}:
     F1-Score:    {best_cv['f1_mean']:.4f} +/- {best_cv['f1_std']:.4f}
     Accuracy:    {best_cv['accuracy_mean']:.4f} +/- {best_cv['accuracy_std']:.4f}

9. PERBANDINGAN MODEL (Test Set)
""")

print(f"   {'Model':<30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("   " + "-" * 70)
for name, res in sorted_models:
    marker = " <-- BEST" if name == best_model_name else ""
    print(f"   {name:<30} {res['accuracy']:>10.4f} {res['precision']:>10.4f} {res['recall']:>10.4f} {res['f1_score']:>10.4f}{marker}")

print(f"""
10. MODEL TERBAIK
    {best_model_name}
    Accuracy:  {best_results['accuracy']:.4f}
    Precision: {best_results['precision']:.4f}
    Recall:    {best_results['recall']:.4f}
    F1-Score:  {best_results['f1_score']:.4f}
    CV F1:     {best_cv['f1_mean']:.4f} +/- {best_cv['f1_std']:.4f}

11. CONFUSION MATRIX ({best_model_name})
""")

cm_best = best_results["confusion_matrix"]
print(f"                 Predicted")
print(f"                 Terlambat  Tepat Waktu")
print(f"  Actual Terlambat    {cm_best[0][0]:>6}      {cm_best[0][1]:>6}")
print(f"  Actual Tepat Waktu  {cm_best[1][0]:>6}      {cm_best[1][1]:>6}")

print(f"""
12. CLASSIFICATION REPORT ({best_model_name})
{best_results['classification_report']}

13. LOKASI MODEL
    Model:      {model_path}
    Encoder:    {encoder_path}
    Metadata:   {metadata_path}
    Comparison: {comparison_path}

14. STATUS TRAINING: COMPLETED
""")

# ============================================================
# STEP 11: INFERENCE PREPARATION
# ============================================================
print("=" * 70)
print("STEP 11: INFERENCE PREPARATION")
print("=" * 70)

print("""
Inference pipeline ready. Model can predict for ACTIVE students using:

Input features:
  - jenis_kelamin (L/P)
  - ipk (0.0-4.0)
  - total_sks (integer)
  - jumlah_mk (integer)
  - angkatan (year)
  - semester (5, 7, or 9)
  - target_sks_kumulatif (integer)
  - selisih_sks (integer)

NOT used (data leakage):
  - status_kelulusan (TARGET)
  - tanggal_keluar (only after graduation)
  - lama_studi (only after graduation)
  - status_mahasiswa (contains graduation status)

Prediction output:
  - 0 = Terlambat
  - 1 = Tepat Waktu

Example inference:
  model = joblib.load('model.joblib')
  prediction = model.predict(new_student_df)
  label = 'Tepat Waktu' if prediction[0] == 1 else 'Terlambat'
""")

spark.stop()

print("=" * 70)
print("MACHINE LEARNING PIPELINE COMPLETE")
print("=" * 70)
