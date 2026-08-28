"""Write gold tables using SQL DDL + INSERT (avoids executor Python worker)."""
import sys
sys.path.insert(0, "/opt/airflow")

import json
import os
import numpy as np
import pandas as pd
import joblib

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, PROJECT_ROOT

spark = get_spark("TugasAkhirNita - Gold Tables Write")
ns = ICEBERG_NAMESPACE

model_a_dir = os.path.join(PROJECT_ROOT, "models", "gaussian_nb_4_features")
model_b_dir = os.path.join(PROJECT_ROOT, "models", "gaussian_nb_8_features")

with open(os.path.join(model_a_dir, "metadata.json")) as f:
    meta_a = json.load(f)
with open(os.path.join(model_b_dir, "metadata.json")) as f:
    meta_b = json.load(f)

# ── 1. gold.model_metrics_final ──
print("1/4 Writing gold.model_metrics_final...")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.model_metrics_final")
spark.sql(f"""
CREATE TABLE {ns}.gold.model_metrics_final (
    model STRING, version STRING,
    cv_mean_accuracy DOUBLE, cv_std_accuracy DOUBLE,
    cv_mean_f1 DOUBLE, cv_std_f1 DOUBLE,
    test_accuracy DOUBLE, test_precision DOUBLE,
    test_recall DOUBLE, test_f1 DOUBLE,
    training_samples BIGINT, test_samples BIGINT,
    features_count INT, features STRING,
    scaler STRING, training_date STRING
) USING iceberg
""")
for name, m in [("4_features", meta_a), ("8_features", meta_b)]:
    feats = ", ".join(m["features"])
    v = m["version"]
    model = f"GaussianNB_{name}"
    td = m["training_date"]
    spark.sql(
        f"INSERT INTO {ns}.gold.model_metrics_final VALUES "
        f"('{model}','{v}',"
        f"{m['cv_accuracy']},0.0,{m['cv_f1']},0.0,"
        f"{m['accuracy']},{m['precision']},{m['recall']},{m['f1_score']},"
        f"{m['training_samples']},{m['test_samples']},"
        f"{len(m['features'])},'{feats}','None','{td}')"
    )
print("  OK")

# ── 2. gold.confusion_matrix_final ──
print("2/4 Writing gold.confusion_matrix_final...")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.confusion_matrix_final")
spark.sql(f"""
CREATE TABLE {ns}.gold.confusion_matrix_final (
    model STRING, actual STRING, predicted STRING, count BIGINT
) USING iceberg
""")
labels = ["Tepat Waktu", "Terlambat"]
for name, m in [("4_features", meta_a), ("8_features", meta_b)]:
    cm = m["confusion_matrix"]
    model = f"GaussianNB_{name}"
    for i, act in enumerate(labels):
        for j, pred in enumerate(labels):
            spark.sql(
                f"INSERT INTO {ns}.gold.confusion_matrix_final VALUES "
                f"('{model}','{act}','{pred}',{cm[i][j]})"
            )
print("  OK")

# ── 3. gold.classification_report_final ──
print("3/4 Writing gold.classification_report_final...")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.classification_report_final")
spark.sql(f"""
CREATE TABLE {ns}.gold.classification_report_final (
    model STRING, class_name STRING,
    precision DOUBLE, recall DOUBLE,
    f1_score DOUBLE, support BIGINT
) USING iceberg
""")
for name, m in [("4_features", meta_a), ("8_features", meta_b)]:
    model = f"GaussianNB_{name}"
    for line in m["classification_report"].strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("macro") or line.startswith("weighted"):
            continue
        parts = line.split()
        if line.startswith("accuracy"):
            acc = parts[1]
            sup = parts[2]
            spark.sql(
                f"INSERT INTO {ns}.gold.classification_report_final VALUES "
                f"('{model}','accuracy',{acc},{acc},{acc},{sup})"
            )
        elif len(parts) >= 5:
            # Determine class name
            if parts[0] == "Tepat":
                cn = "Tepat Waktu"
                vals = parts[2:]
            elif parts[0] == "Terlambat":
                cn = "Terlambat"
                vals = parts[1:]
            elif parts[0] == "accuracy":
                continue
            else:
                cn = parts[0]
                vals = parts[1:]
            if cn in ("Tepat Waktu", "Terlambat"):
                spark.sql(
                    f"INSERT INTO {ns}.gold.classification_report_final VALUES "
                    f"('{model}','{cn}',{vals[0]},{vals[1]},{vals[2]},{vals[3]})"
                )
print("  OK")

# ── 4. gold.prediction_by_angkatan_final ──
print("4/4 Writing gold.prediction_by_angkatan_final...")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.prediction_by_angkatan_final")
spark.sql(f"""
CREATE TABLE {ns}.gold.prediction_by_angkatan_final (
    model STRING, angkatan BIGINT,
    total_mahasiswa BIGINT,
    prediksi_tepat_waktu BIGINT, prediksi_terlambat BIGINT,
    persentase_tepat_waktu DOUBLE, persentase_terlambat DOUBLE
) USING iceberg
""")
model_a = joblib.load(os.path.join(model_a_dir, "model.joblib"))
model_b = joblib.load(os.path.join(model_b_dir, "model.joblib"))

inf = spark.table(f"{ns}.feature_store.inference_dataset").toPandas()
dim = spark.table(f"{ns}.gold.dim_mahasiswa").toPandas()

X_a = inf[["angkatan", "ip", "sks", "jumlah_mk"]].values
inf["pred_4"] = np.where(model_a.predict(X_a) == 0, "Tepat Waktu", "Terlambat")

merged = inf.merge(dim[["id_mahasiswa", "jenis_kelamin", "ipk", "total_sks"]], on="id_mahasiswa", how="left")
merged["sks_seharusnya"] = merged["jumlah_mk"] * 24
merged["selisih_sks"] = merged["total_sks"] - merged["sks_seharusnya"]
merged["jk_enc"] = merged["jenis_kelamin"].map({"P": 0, "L": 1}).fillna(0).astype(int)
X_b = merged[["jk_enc", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]].values
inf["pred_8"] = np.where(model_b.predict(X_b) == 0, "Tepat Waktu", "Terlambat")

for model_name, col in [("GaussianNB_4_features", "pred_4"), ("GaussianNB_8_features", "pred_8")]:
    for angkatan in sorted(inf["angkatan"].unique()):
        sub = inf[inf["angkatan"] == angkatan]
        total = len(sub)
        tw = int((sub[col] == "Tepat Waktu").sum())
        tl = int((sub[col] == "Terlambat").sum())
        ptw = round(tw / total * 100, 2) if total else 0
        ptl = round(tl / total * 100, 2) if total else 0
        spark.sql(
            f"INSERT INTO {ns}.gold.prediction_by_angkatan_final VALUES "
            f"('{model_name}',{int(angkatan)},{total},{tw},{tl},{ptw},{ptl})"
        )
print("  OK")

print("\nAll 4 gold tables written successfully!")
