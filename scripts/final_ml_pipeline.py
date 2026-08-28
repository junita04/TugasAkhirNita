"""
FINAL ML Pipeline — Dual Model Training & Evaluation
=====================================================
Model A: 4 features (angkatan, ip, sks, jumlah_mk) — from training_dataset
Model B: 8 features (jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk,
         sks_seharusnya, selisih_sks) — from dim_mahasiswa + fact_khs JOIN

Source:
  - feature_store.training_dataset (4 features, already exists)
  - gold.dim_mahasiswa + gold.fact_khs (for 8-feature model)
  - sks_seharusnya = jumlah_mk * 24 (24 SKS per MK average)
  - selisih_sks = total_sks - sks_seharusnya

No StandardScaler. No SMOTE for baseline. GaussianNB for both.
"""
import sys
sys.path.insert(0, "/opt/airflow")

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

import pyspark.sql.functions as F

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, make_scorer,
)

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, PROJECT_ROOT

# ============================================================
# CONFIGURATION
# ============================================================

POSITIVE_CLASS = "Tepat Waktu"
TARGET_COLUMN = "status_kelulusan"
ID_COLUMN = "id_mahasiswa"

MODEL_A_FEATURES = ["angkatan", "ip", "sks", "jumlah_mk"]
MODEL_B_FEATURES = [
    "jenis_kelamin", "angkatan", "ip", "ipk",
    "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks",
]

RANDOM_STATE = 42
TEST_SIZE = 0.20
N_SPLITS = 10

MODEL_DIR_A = os.path.join(PROJECT_ROOT, "models", "gaussian_nb_4_features")
MODEL_DIR_B = os.path.join(PROJECT_ROOT, "models", "gaussian_nb_8_features")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# ============================================================
# DATA LOADING
# ============================================================

def load_model_a_dataset(spark):
    """Load 4-feature dataset from feature_store.training_dataset."""
    print("=" * 60)
    print("LOADING MODEL A DATASET (4 features)")
    print("=" * 60)

    df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
    pdf = df.toPandas()

    print(f"Table    : {ICEBERG_NAMESPACE}.feature_store.training_dataset")
    print(f"Rows     : {len(pdf)}")
    print(f"Columns  : {list(pdf.columns)}")
    print(f"Label    : {pdf[TARGET_COLUMN].value_counts().to_dict()}")

    return pdf


def load_model_b_dataset(spark):
    """Load 8-feature dataset from dim_mahasiswa JOIN fact_khs."""
    print("\n" + "=" * 60)
    print("LOADING MODEL B DATASET (8 features)")
    print("=" * 60)

    dim = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")
    fact = spark.table(f"{ICEBERG_NAMESPACE}.gold.fact_khs")

    # Join
    joined = dim.join(fact, on="id_mahasiswa", how="left")

    # Filter LULUS students only (for training)
    lulus = joined.filter(F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS")

    # Add derived features
    # angkatan = year(tanggal_masuk)
    lulus = lulus.withColumn("angkatan", F.year(F.col("tanggal_masuk")))

    # sks_seharusnya = jumlah_mk * 24 (24 SKS per MK average)
    lulus = lulus.withColumn("sks_seharusnya", F.col("jumlah_mk") * 24)

    # selisih_sks = total_sks - sks_seharusnya
    lulus = lulus.withColumn("selisih_sks", F.col("total_sks") - F.col("sks_seharusnya"))

    # lama_studi = tanggal_keluar - tanggal_masuk (days)
    lulus = lulus.withColumn(
        "lama_studi",
        F.datediff(F.col("tanggal_keluar"), F.col("tanggal_masuk")),
    )

    # Label: Tepat Waktu if lama_studi <= 1460 days (4 years)
    lulus = lulus.withColumn(
        TARGET_COLUMN,
        F.when(F.col("lama_studi") <= 1460, F.lit("Tepat Waktu"))
        .otherwise(F.lit("Terlambat")),
    )

    # Drop NULL features
    feature_cols = ["ip", "jenis_kelamin", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]
    valid = lulus.dropna(subset=feature_cols)

    # Deduplicate
    valid = valid.dropDuplicates(["id_mahasiswa"])

    # Select required columns
    select_cols = ["id_mahasiswa"] + MODEL_B_FEATURES + [TARGET_COLUMN]
    result = valid.select(*select_cols)

    pdf = result.toPandas()

    print(f"Source   : {ICEBERG_NAMESPACE}.gold.dim_mahasiswa LEFT JOIN {ICEBERG_NAMESPACE}.gold.fact_khs")
    print(f"Filter   : status_mahasiswa = LULUS")
    print(f"Rows     : {len(pdf)}")
    print(f"Columns  : {list(pdf.columns)}")
    print(f"Label    : {pdf[TARGET_COLUMN].value_counts().to_dict()}")

    # Show null counts
    null_counts = {c: int(pdf[c].isnull().sum()) for c in MODEL_B_FEATURES}
    print(f"Nulls    : {null_counts}")

    return pdf


# ============================================================
# TRAINING & EVALUATION
# ============================================================

def prepare_X_y(pdf, feature_columns, target_col=TARGET_COLUMN):
    """Prepare X, y arrays."""
    X = pdf[feature_columns].copy()

    # Encode jenis_kelamin if present
    if "jenis_kelamin" in X.columns:
        X["jenis_kelamin"] = X["jenis_kelamin"].map({"P": 0, "L": 1}).fillna(0).astype(int)

    # Encode target
    class_mapping = {label: idx for idx, label in enumerate(sorted(pdf[target_col].unique()))}
    y = pdf[target_col].map(class_mapping).astype(int)

    return X.values, y.values, class_mapping


def train_and_evaluate(X, y, model_name, feature_names):
    """Train GaussianNB and evaluate with CV + holdout."""
    print("\n" + "=" * 60)
    print(f"TRAINING: {model_name}")
    print(f"Features: {feature_names}")
    print(f"X shape: {X.shape}")
    print(f"y distribution: TW={int((y == 0).sum())}, TL={int((y == 1).sum())}")
    print("=" * 60)

    # Split
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y,
    )
    print(f"Development (80%): {len(X_dev)} records")
    print(f"Holdout test (20%): {len(X_test)} records")

    # CV
    scoring = {
        "accuracy": make_scorer(accuracy_score),
        "precision": make_scorer(precision_score, pos_label=0),
        "recall": make_scorer(recall_score, pos_label=0),
        "f1": make_scorer(f1_score, pos_label=0),
    }
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    model = GaussianNB()
    cv_results = cross_validate(model, X_dev, y_dev, cv=cv, scoring=scoring, n_jobs=1)

    cv_acc = cv_results["test_accuracy"]
    cv_prec = cv_results["test_precision"]
    cv_rec = cv_results["test_recall"]
    cv_f1 = cv_results["test_f1"]

    print("\n--- Cross Validation (10-Fold) ---")
    for fold in range(N_SPLITS):
        print(f"  Fold {fold+1:>2}: acc={cv_acc[fold]:.4f} prec={cv_prec[fold]:.4f} rec={cv_rec[fold]:.4f} f1={cv_f1[fold]:.4f}")

    cv_summary = {
        "accuracy": {"mean": float(cv_acc.mean()), "std": float(cv_acc.std())},
        "precision": {"mean": float(cv_prec.mean()), "std": float(cv_prec.std())},
        "recall": {"mean": float(cv_rec.mean()), "std": float(cv_rec.std())},
        "f1": {"mean": float(cv_f1.mean()), "std": float(cv_f1.std())},
    }

    print(f"\nCV Accuracy : {cv_summary['accuracy']['mean']:.4f} +/- {cv_summary['accuracy']['std']:.4f}")
    print(f"CV Precision: {cv_summary['precision']['mean']:.4f} +/- {cv_summary['precision']['std']:.4f}")
    print(f"CV Recall   : {cv_summary['recall']['mean']:.4f} +/- {cv_summary['recall']['std']:.4f}")
    print(f"CV F1       : {cv_summary['f1']['mean']:.4f} +/- {cv_summary['f1']['std']:.4f}")

    # Holdout
    model.fit(X_dev, y_dev)
    y_pred = model.predict(X_test)

    holdout = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, pos_label=0)),
        "recall": float(recall_score(y_test, y_pred, pos_label=0)),
        "f1": float(f1_score(y_test, y_pred, pos_label=0)),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_test, y_pred, labels=[0, 1],
            target_names=["Tepat Waktu", "Terlambat"],
            digits=4, zero_division=0,
        ),
    }

    print("\n--- Holdout Test (20%) ---")
    print(f"Accuracy : {holdout['accuracy']:.4f}")
    print(f"Precision: {holdout['precision']:.4f}")
    print(f"Recall   : {holdout['recall']:.4f}")
    print(f"F1       : {holdout['f1']:.4f}")
    cm = holdout["confusion_matrix"]
    print(f"Confusion Matrix:")
    print(f"  [[TN={cm[0][0]}, FP={cm[0][1]}],")
    print(f"   [FN={cm[1][0]}, TP={cm[1][1]}]]")
    print(f"\n{holdout['classification_report']}")

    # Final model on full data
    final_model = GaussianNB()
    final_model.fit(X, y)
    print(f"Final model fitted on {len(X)} records.")

    return {
        "model": final_model,
        "cv_summary": cv_summary,
        "holdout": holdout,
        "dev_size": len(X_dev),
        "test_size": len(X_test),
        "X_test": X_test,
        "y_test": y_test,
        "y_pred": y_pred,
    }


# ============================================================
# SAVE
# ============================================================

def save_model(model_dir, model, feature_names, result, model_label):
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.joblib")
    metadata_path = os.path.join(model_dir, "metadata.json")

    joblib.dump(model, model_path)

    metadata = {
        "model_name": "GaussianNB",
        "model_type": "GaussianNB",
        "version": f"final_{model_label}",
        "features": feature_names,
        "target": TARGET_COLUMN,
        "target_mapping": {"Tepat Waktu": 0, "Terlambat": 1},
        "scaler": None,
        "preprocessing": [],
        "training_samples": result["dev_size"] + result["test_size"],
        "test_samples": result["test_size"],
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "cv_folds": N_SPLITS,
        "accuracy": result["holdout"]["accuracy"],
        "precision": result["holdout"]["precision"],
        "recall": result["holdout"]["recall"],
        "f1_score": result["holdout"]["f1"],
        "cv_accuracy": result["cv_summary"]["accuracy"]["mean"],
        "cv_f1": result["cv_summary"]["f1"]["mean"],
        "confusion_matrix": result["holdout"]["confusion_matrix"],
        "classification_report": result["holdout"]["classification_report"],
        "artifact_path": model_path,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Model saved : {model_path}")
    print(f"Metadata    : {metadata_path}")
    return metadata


def save_results(result_a, result_b, features_a, features_b):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Comparison
    comparison = pd.DataFrame({
        "metric": ["Accuracy", "Precision", "Recall", "F1-Score",
                    "CV Accuracy", "CV F1", "Training Samples", "Test Samples", "Features"],
        "model_4_features": [
            result_a["holdout"]["accuracy"], result_a["holdout"]["precision"],
            result_a["holdout"]["recall"], result_a["holdout"]["f1"],
            result_a["cv_summary"]["accuracy"]["mean"], result_a["cv_summary"]["f1"]["mean"],
            result_a["dev_size"] + result_a["test_size"], result_a["test_size"], len(features_a),
        ],
        "model_8_features": [
            result_b["holdout"]["accuracy"], result_b["holdout"]["precision"],
            result_b["holdout"]["recall"], result_b["holdout"]["f1"],
            result_b["cv_summary"]["accuracy"]["mean"], result_b["cv_summary"]["f1"]["mean"],
            result_b["dev_size"] + result_b["test_size"], result_b["test_size"], len(features_b),
        ],
    })
    comparison.to_csv(os.path.join(RESULTS_DIR, "final_model_comparison.csv"), index=False)

    for name, result in [("4_features", result_a), ("8_features", result_b)]:
        cm = result["holdout"]["confusion_matrix"]
        cm_df = pd.DataFrame(cm, index=["Tepat Waktu", "Terlambat"], columns=["Tepat Waktu", "Terlambat"])
        cm_df.to_csv(os.path.join(RESULTS_DIR, f"model_{name}_confusion_matrix.csv"))

        with open(os.path.join(RESULTS_DIR, f"model_{name}_classification_report.csv"), "w") as f:
            f.write(result["holdout"]["classification_report"])

    print("Results saved.")


def write_gold_tables(spark, result_a, result_b, features_a, features_b):
    print("\n" + "=" * 60)
    print("WRITING GOLD TABLES FOR SUPERSET")
    print("=" * 60)

    # 1. gold.model_metrics_final
    metrics_data = []
    for name, result, features in [("4_features", result_a, features_a), ("8_features", result_b, features_b)]:
        metrics_data.append({
            "model": f"GaussianNB_{name}",
            "version": f"final_{name}",
            "cv_mean_accuracy": result["cv_summary"]["accuracy"]["mean"],
            "cv_std_accuracy": result["cv_summary"]["accuracy"]["std"],
            "cv_mean_f1": result["cv_summary"]["f1"]["mean"],
            "cv_std_f1": result["cv_summary"]["f1"]["std"],
            "test_accuracy": result["holdout"]["accuracy"],
            "test_precision": result["holdout"]["precision"],
            "test_recall": result["holdout"]["recall"],
            "test_f1": result["holdout"]["f1"],
            "training_samples": result["dev_size"] + result["test_size"],
            "test_samples": result["test_size"],
            "features_count": len(features),
            "features": ", ".join(features),
            "scaler": "None",
            "training_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        })
    metrics_df = spark.createDataFrame(pd.DataFrame(metrics_data))
    metrics_df.writeTo(f"{ICEBERG_NAMESPACE}.gold.model_metrics_final").using("iceberg").createOrReplace()
    print("Written: gold.model_metrics_final")

    # 2. gold.confusion_matrix_final
    cm_data = []
    for name, result in [("4_features", result_a), ("8_features", result_b)]:
        cm = result["holdout"]["confusion_matrix"]
        labels = ["Tepat Waktu", "Terlambat"]
        for i, actual in enumerate(labels):
            for j, predicted in enumerate(labels):
                cm_data.append({
                    "model": f"GaussianNB_{name}",
                    "actual": actual,
                    "predicted": predicted,
                    "count": int(cm[i][j]),
                })
    cm_df = spark.createDataFrame(pd.DataFrame(cm_data))
    cm_df.writeTo(f"{ICEBERG_NAMESPACE}.gold.confusion_matrix_final").using("iceberg").createOrReplace()
    print("Written: gold.confusion_matrix_final")

    # 3. gold.classification_report_final
    cr_data = []
    for name, result in [("4_features", result_a), ("8_features", result_b)]:
        report = result["holdout"]["classification_report"]
        for line in report.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("accuracy"):
                parts = line.split()
                cr_data.append({
                    "model": f"GaussianNB_{name}", "class": "accuracy",
                    "precision": float(parts[1]), "recall": float(parts[1]),
                    "f1_score": float(parts[1]), "support": int(parts[3]),
                })
                continue
            if line.startswith("weighted") or line.startswith("macro"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                class_name = parts[0] + (" " + parts[1] if parts[1] in ["Waktu", "Lambat"] else "")
                if class_name in ["Tepat Waktu", "Terlambat"]:
                    cr_data.append({
                        "model": f"GaussianNB_{name}", "class": class_name,
                        "precision": float(parts[-4]), "recall": float(parts[-3]),
                        "f1_score": float(parts[-2]), "support": int(parts[-1]),
                    })
    cr_df = spark.createDataFrame(pd.DataFrame(cr_data))
    cr_df.writeTo(f"{ICEBERG_NAMESPACE}.gold.classification_report_final").using("iceberg").createOrReplace()
    print("Written: gold.classification_report_final")

    # 4. gold.prediction_by_angkatan_final
    inf_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset").toPandas()

    # Load both models and predict
    model_a = joblib.load(os.path.join(PROJECT_ROOT, "models", "gaussian_nb_4_features", "model.joblib"))
    model_b = joblib.load(os.path.join(PROJECT_ROOT, "models", "gaussian_nb_8_features", "model.joblib"))

    # Model A predictions
    X_a = inf_df[["angkatan", "ip", "sks", "jumlah_mk"]].values
    preds_a = model_a.predict(X_a)

    # Model B predictions (need to join with dim_mahasiswa for extra features)
    dim_pdf = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa").toPandas()
    inf_with_dim = inf_df.merge(dim_pdf[["id_mahasiswa", "jenis_kelamin", "ipk", "total_sks"]], on="id_mahasiswa", how="left")
    inf_with_dim["sks_seharusnya"] = inf_with_dim["jumlah_mk"] * 24
    inf_with_dim["selisih_sks"] = inf_with_dim["total_sks"] - inf_with_dim["sks_seharusnya"]
    inf_with_dim["jenis_kelamin_enc"] = inf_with_dim["jenis_kelamin"].map({"P": 0, "L": 1}).fillna(0).astype(int)

    X_b = inf_with_dim[["jenis_kelamin_enc", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]].values
    preds_b = model_b.predict(X_b)

    inf_df["prediksi_4fitur"] = np.where(preds_a == 0, "Tepat Waktu", "Terlambat")
    inf_df["prediksi_8fitur"] = np.where(preds_b == 0, "Tepat Waktu", "Terlambat")

    # Aggregate by angkatan
    angkatan_data = []
    for model_name, pred_col in [("GaussianNB_4_features", "prediksi_4fitur"), ("GaussianNB_8_features", "prediksi_8fitur")]:
        for angkatan in sorted(inf_df["angkatan"].unique()):
            subset = inf_df[inf_df["angkatan"] == angkatan]
            total = len(subset)
            tw = int((subset[pred_col] == "Tepat Waktu").sum())
            tl = int((subset[pred_col] == "Terlambat").sum())
            angkatan_data.append({
                "model": model_name,
                "angkatan": int(angkatan),
                "total_mahasiswa": total,
                "prediksi_tepat_waktu": tw,
                "prediksi_terlambat": tl,
                "persentase_tepat_waktu": round(tw / total * 100, 2) if total > 0 else 0,
                "persentase_terlambat": round(tl / total * 100, 2) if total > 0 else 0,
            })
    angkatan_df = spark.createDataFrame(pd.DataFrame(angkatan_data))
    angkatan_df.writeTo(f"{ICEBERG_NAMESPACE}.gold.prediction_by_angkatan_final").using("iceberg").createOrReplace()
    print("Written: gold.prediction_by_angkatan_final")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("FINAL ML PIPELINE — DUAL MODEL TRAINING & EVALUATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    spark = get_spark("TugasAkhirNita - Final ML Pipeline")

    # Load datasets
    pdf_a = load_model_a_dataset(spark)
    pdf_b = load_model_b_dataset(spark)

    # Prepare X, y for Model A
    X_a, y_a, mapping_a = prepare_X_y(pdf_a, MODEL_A_FEATURES)
    print(f"\nModel A: {len(MODEL_A_FEATURES)} features, {len(X_a)} samples")
    print(f"Class mapping: {mapping_a}")

    # Prepare X, y for Model B
    X_b, y_b, mapping_b = prepare_X_y(pdf_b, MODEL_B_FEATURES)
    print(f"\nModel B: {len(MODEL_B_FEATURES)} features, {len(X_b)} samples")
    print(f"Class mapping: {mapping_b}")

    # Train & evaluate
    result_a = train_and_evaluate(X_a, y_a, "Model A (4 Features)", MODEL_A_FEATURES)
    result_b = train_and_evaluate(X_b, y_b, "Model B (8 Features)", MODEL_B_FEATURES)

    # Save models
    print("\n" + "=" * 60)
    print("SAVING MODELS")
    print("=" * 60)
    save_model(MODEL_DIR_A, result_a["model"], MODEL_A_FEATURES, result_a, "4_features")
    save_model(MODEL_DIR_B, result_b["model"], MODEL_B_FEATURES, result_b, "8_features")

    # Save results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    save_results(result_a, result_b, MODEL_A_FEATURES, MODEL_B_FEATURES)

    # Write gold tables
    write_gold_tables(spark, result_a, result_b, MODEL_A_FEATURES, MODEL_B_FEATURES)

    # Final comparison
    print("\n" + "=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)
    print(f"{'Metric':<25} {'4 Features':>15} {'8 Features':>15}")
    print("-" * 55)
    print(f"{'Accuracy':<25} {result_a['holdout']['accuracy']:>15.4f} {result_b['holdout']['accuracy']:>15.4f}")
    print(f"{'Precision':<25} {result_a['holdout']['precision']:>15.4f} {result_b['holdout']['precision']:>15.4f}")
    print(f"{'Recall':<25} {result_a['holdout']['recall']:>15.4f} {result_b['holdout']['recall']:>15.4f}")
    print(f"{'F1-Score':<25} {result_a['holdout']['f1']:>15.4f} {result_b['holdout']['f1']:>15.4f}")
    print(f"{'CV Accuracy':<25} {result_a['cv_summary']['accuracy']['mean']:>15.4f} {result_b['cv_summary']['accuracy']['mean']:>15.4f}")
    print(f"{'CV F1':<25} {result_a['cv_summary']['f1']['mean']:>15.4f} {result_b['cv_summary']['f1']['mean']:>15.4f}")
    print(f"{'Training Samples':<25} {result_a['dev_size'] + result_a['test_size']:>15} {result_b['dev_size'] + result_b['test_size']:>15}")
    print(f"{'Test Samples':<25} {result_a['test_size']:>15} {result_b['test_size']:>15}")
    print(f"{'Features':<25} {len(MODEL_A_FEATURES):>15} {len(MODEL_B_FEATURES):>15}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
