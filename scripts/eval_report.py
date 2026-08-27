"""Quick evaluation report"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import joblib
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

spark = SparkSession.builder.appName("TA_Evaluation").master("local[*]").config("spark.driver.extraClassPath", "/opt/airflow/jars/*").config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000").config("spark.hadoop.fs.s3a.access.key", "minioadmin").config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password").config("spark.hadoop.fs.s3a.path.style.access", "true").config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem").config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false").config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem").config("spark.hadoop.fs.s3.endpoint", "http://minio:9000").config("spark.hadoop.fs.s3.access.key", "minioadmin").config("spark.hadoop.fs.s3.secret.key", "minioadmin-password").config("spark.hadoop.fs.s3.path.style.access", "true").config("spark.hadoop.fs.s3.connection.ssl.enabled", "false").config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions").config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog").config("spark.sql.catalog.iceberg.type", "hive").config("spark.sql.catalog.iceberg.uri", "thrift://hive-metastore:9083").config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg").config("spark.driver.memory", "2g").config("spark.eventLog.enabled", "true").config("spark.eventLog.dir", "file:///spark-events").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df_fs = spark.table("iceberg.feature_store.feature_store_graduation_prediction")
pdf_fs = df_fs.toPandas()

FEATURE_COLS = ["jenis_kelamin", "ipk", "total_sks", "jumlah_mk", "angkatan", "semester", "target_sks_kumulatif", "selisih_sks"]
TARGET_COL = "status_kelulusan"

X = pdf_fs[FEATURE_COLS].copy()
y_raw = pdf_fs[TARGET_COL].copy()
le = LabelEncoder()
y = le.fit_transform(y_raw)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

categorical_features = ["jenis_kelamin"]
numerical_features = [c for c in FEATURE_COLS if c not in categorical_features]
preprocessor = ColumnTransformer([("num", StandardScaler(), numerical_features), ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features)])

final_pipe = Pipeline([("preprocessor", preprocessor), ("classifier", GaussianNB())])
final_pipe.fit(X_train, y_train)
y_pred_test = final_pipe.predict(X_test)

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
fold_results = []
for fold_idx, (tr_idx, val_idx) in enumerate(cv.split(X, y), 1):
    pipe = Pipeline([("preprocessor", preprocessor), ("classifier", GaussianNB())])
    pipe.fit(X.iloc[tr_idx], y[tr_idx])
    yp = pipe.predict(X.iloc[val_idx])
    acc = accuracy_score(y[val_idx], yp)
    f1 = f1_score(y[val_idx], yp, average="weighted")
    fold_results.append({"fold": fold_idx, "accuracy": acc, "f1": f1})

y_pred_train = final_pipe.predict(X_train)

df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")
df_aktif = df_gold.filter((F.col("status_mahasiswa") == "AKTIF") & (F.col("semester") >= 5) & (F.col("ipk").isNotNull()) & (F.col("total_sks").isNotNull()))
pdf_aktif = df_aktif.toPandas()
X_aktif = pdf_aktif[FEATURE_COLS].copy()
pred_aktif = final_pipe.predict(X_aktif)

print("=" * 70)
print("EVALUASI MODEL — GAUSSIAN NAIVE BAYES")
print("=" * 70)

print("\n1. CONFUSION MATRIX (Test Set)")
cm = confusion_matrix(y_test, y_pred_test)
print("                 Predicted")
print("                 Tepat Waktu  Terlambat")
print("  Actual TW         %6d      %6d" % (cm[0][0], cm[0][1]))
print("  Actual TL         %6d      %6d" % (cm[1][0], cm[1][1]))

print("\n2. METRIK EVALUASI (Test Set)")
print("  Accuracy:   %.4f" % accuracy_score(y_test, y_pred_test))
print("  Precision:  %.4f" % precision_score(y_test, y_pred_test, average="weighted"))
print("  Recall:     %.4f" % recall_score(y_test, y_pred_test, average="weighted"))
print("  F1-Score:   %.4f" % f1_score(y_test, y_pred_test, average="weighted"))

print("\n3. CLASSIFICATION REPORT (Test Set)")
print(classification_report(y_test, y_pred_test, target_names=le.classes_))

print("4. 10-FOLD CROSS VALIDATION")
print("%-6s %10s %10s" % ("Fold", "Accuracy", "F1-Score"))
print("-" * 30)
for r in fold_results:
    print("Fold %-3d %10.4f %10.4f" % (r["fold"], r["accuracy"], r["f1"]))
print("-" * 30)
mean_acc = np.mean([r["accuracy"] for r in fold_results])
std_acc = np.std([r["accuracy"] for r in fold_results])
mean_f1 = np.mean([r["f1"] for r in fold_results])
std_f1 = np.std([r["f1"] for r in fold_results])
print("%-6s %10.4f %10.4f" % ("Mean", mean_acc, mean_f1))
print("%-6s %10.4f %10.4f" % ("Std", std_acc, std_f1))

print("\n5. DISTRIBUSI ANGKATAN — TRAINING SET")
pdf_train = X_train.copy()
pdf_train["angkatan"] = X_train["angkatan"].astype(int)
train_ang = pdf_train.groupby("angkatan").size().reset_index(name="count")
print("%-10s %8s" % ("Angkatan", "Jumlah"))
print("-" * 20)
for _, r in train_ang.iterrows():
    print("%-10d %8d" % (int(r["angkatan"]), int(r["count"])))
print("%-10s %8d" % ("TOTAL", int(train_ang["count"].sum())))

print("\n6. DISTRIBUSI ANGKATAN — TEST SET")
pdf_test = X_test.copy()
pdf_test["angkatan"] = X_test["angkatan"].astype(int)
test_ang = pdf_test.groupby("angkatan").size().reset_index(name="count")
print("%-10s %8s" % ("Angkatan", "Jumlah"))
print("-" * 20)
for _, r in test_ang.iterrows():
    print("%-10d %8d" % (int(r["angkatan"]), int(r["count"])))
print("%-10s %8d" % ("TOTAL", int(test_ang["count"].sum())))

print("\n7. DISTRIBUSI ANGKATAN — SELURUH DATA (Feature Store)")
pdf_all = X.copy()
pdf_all["angkatan"] = X["angkatan"].astype(int)
all_ang = pdf_all.groupby("angkatan").size().reset_index(name="count")
print("%-10s %8s" % ("Angkatan", "Jumlah"))
print("-" * 20)
for _, r in all_ang.iterrows():
    print("%-10d %8d" % (int(r["angkatan"]), int(r["count"])))
print("%-10s %8d" % ("TOTAL", int(all_ang["count"].sum())))

print("\n8. DISTRIBUSI ANGKATAN — PREDIKSI MAHASISWA AKTIF")
pdf_aktif_out = pdf_aktif.copy()
pdf_aktif_out["angkatan"] = pdf_aktif["angkatan"].astype(int)
pdf_aktif_out["prediksi"] = [le.classes_[i] for i in pred_aktif]
aktif_ang = pdf_aktif_out.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    pred_tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    pred_tl=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()
print("%-10s %8s %10s %10s" % ("Angkatan", "Total", "Pred TW", "Pred TL"))
print("-" * 42)
for _, r in aktif_ang.iterrows():
    print("%-10d %8d %10d %10d" % (int(r["angkatan"]), int(r["total"]), int(r["pred_tw"]), int(r["pred_tl"])))
print("-" * 42)
print("%-10s %8d %10d %10d" % ("TOTAL", int(aktif_ang["total"].sum()), int(aktif_ang["pred_tw"].sum()), int(aktif_ang["pred_tl"].sum())))

spark.stop()
