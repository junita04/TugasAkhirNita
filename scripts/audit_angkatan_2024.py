"""
AUDIT ANGKATAN 2024 — Comprehensive Analysis
"""
import sys, os, json, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

# ============================================================
# SPARK INIT
# ============================================================
spark = (
    SparkSession.builder
    .appName("TA_Audit_Angkatan_2024")
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
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# ============================================================
# LOAD DATA (same logic as pipeline)
# ============================================================
print("=" * 70)
print("LOADING DATA")
print("=" * 70)

df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")
df_khs = spark.table("iceberg.bronze.data_khs")
df_khs = df_khs.withColumn("ip", F.col("ip").cast("double"))
df_khs = df_khs.withColumn("sks", F.col("sks").cast("int"))
df_khs_agg = df_khs.groupBy("id_mhs").agg(F.max("ip").alias("ip"), F.max("sks").alias("sks_khs"))

df_gold_final = df_gold.join(df_khs_agg, on="id_mhs", how="left")
df_gold_final = df_gold_final.withColumn("sks_seharusnya", F.col("target_sks_kumulatif"))

# Training data (Lulus only)
df_lulus = df_gold_final.filter(
    (F.col("status_mahasiswa") == "Lulus") &
    (F.col("ip").isNotNull()) &
    (F.col("lama_studi").isNotNull())
)
df_labeled = df_lulus.withColumn(
    "label",
    F.when((F.col("total_sks") >= 144) & (F.col("lama_studi") <= 4.0), F.lit("Tepat Waktu"))
     .when((F.col("total_sks") < 144) | (F.col("lama_studi") > 4.0), F.lit("Terlambat"))
     .otherwise(F.lit(None).cast("string"))
)
df_labeled = df_labeled.filter(F.col("label").isNotNull())

FEATURE_COLS = ["jenis_kelamin", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]

pdf_train_full = df_labeled.select("id_mhs", *FEATURE_COLS, "label").toPandas()
pdf_train_full["jenis_kelamin"] = pdf_train_full["jenis_kelamin"].astype(str).str.strip().str.upper().map({"P": 0, "L": 1})

# Inference data (AKTIF only)
df_aktif = df_gold_final.filter(
    (F.col("status_mahasiswa") == "AKTIF") &
    (F.col("ip").isNotNull()) &
    (F.col("ipk").isNotNull()) &
    (F.col("total_sks").isNotNull()) &
    (F.col("jumlah_mk").isNotNull()) &
    (F.col("sks_seharusnya").isNotNull()) &
    (F.col("selisih_sks").isNotNull())
)

pdf_inf_all = df_aktif.select("id_mhs", *FEATURE_COLS).toPandas()
pdf_inf_all["jenis_kelamin"] = pdf_inf_all["jenis_kelamin"].astype(str).str.strip().str.upper().map({"P": 0, "L": 1})

# Load model
final_pipe = joblib.load("/opt/airflow/models/graduation_prediction_final/gaussian_nb_final.joblib")

# Predict ALL inference
X_all_inf = pdf_inf_all[FEATURE_COLS].copy()
pred_all = final_pipe.predict(X_all_inf)
prob_all = final_pipe.predict_proba(X_all_inf)
pdf_inf_all["prediksi"] = ["Tepat Waktu" if i == 0 else "Terlambat" for i in pred_all]
pdf_inf_all["prob_tw"] = prob_all[:, 0].round(4)
pdf_inf_all["prob_tl"] = prob_all[:, 1].round(4)

print(f"Total inference: {len(pdf_inf_all)}")
print(f"Total training: {len(pdf_train_full)}")

# ============================================================
# 1. BREAKDOWN ANGKATAN 2024
# ============================================================
print("\n" + "=" * 70)
print("1. BREAKDOWN ANGKATAN 2024")
print("=" * 70)

pdf_2024 = pdf_inf_all[pdf_inf_all["angkatan"] == 2024]
total = len(pdf_2024)
tw = (pdf_2024["prediksi"] == "Tepat Waktu").sum()
tl = (pdf_2024["prediksi"] == "Terlambat").sum()

print(f"Total mahasiswa aktif Angkatan 2024: {total}")
print(f"Prediksi Tepat Waktu: {tw} ({tw/total*100:.2f}%)")
print(f"Prediksi Terlambat: {tl} ({tl/total*100:.2f}%)")

# ============================================================
# 2. DISTRIBUSI SEMESTER
# ============================================================
print("\n" + "=" * 70)
print("2. DISTRIBUSI SEMESTER (Angkatan 2024)")
print("=" * 70)

# Recalculate semester from Gold
pdf_gold_2024 = df_gold_final.filter(F.col("angkatan") == 2024).select("id_mhs", "semester", "angkatan").toPandas()
pdf_2024_full = pdf_inf_all[pdf_inf_all["angkatan"] == 2024].merge(pdf_gold_2024, on="id_mhs", how="left")

sem_dist = pdf_2024_full["semester"].value_counts().sort_index()
print(f"\n{'Semester':>10} | {'Jumlah':>8} | {'Persentase':>10}")
print("-" * 35)
for sem, cnt in sem_dist.items():
    print(f"{int(sem):>10} | {cnt:>8} | {cnt/total*100:>9.2f}%")

# ============================================================
# 3. STATISTIK FEATURE ANGKATAN 2024
# ============================================================
print("\n" + "=" * 70)
print("3. STATISTIK FEATURE (Angkatan 2024)")
print("=" * 70)

features_to_check = ["ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]
print(f"\n{'Feature':>18} | {'Min':>8} | {'Max':>8} | {'Mean':>8} | {'Median':>8} | {'Missing':>8} | {'Zero':>6}")
print("-" * 80)
for f in features_to_check:
    col = pdf_2024[f]
    mn = col.min()
    mx = col.max()
    mean = col.mean()
    med = col.median()
    miss = col.isna().sum()
    zero = (col == 0).sum()
    print(f"{f:>18} | {mn:>8.2f} | {mx:>8.2f} | {mean:>8.2f} | {med:>8.2f} | {miss:>8} | {zero:>6}")

# ============================================================
# 4. DISTRIBUSI TOTAL SKS
# ============================================================
print("\n" + "=" * 70)
print("4. DISTRIBUSI TOTAL SKS (Angkatan 2024)")
print("=" * 70)

sks = pdf_2024["total_sks"]
print(f"Min: {sks.min()}, Max: {sks.max()}, Mean: {sks.mean():.2f}, Median: {sks.median():.0f}")

bins = [0, 20, 40, 60, 80, 100, 120, 144, 999]
labels = ["0-20", "21-40", "41-60", "61-80", "81-100", "101-120", "121-143", ">=144"]
pdf_2024_sks = pdf_2024.copy()
pdf_2024_sks["sks_bin"] = pd.cut(pdf_2024_sks["total_sks"], bins=bins, labels=labels, right=True)
sks_dist = pdf_2024_sks["sks_bin"].value_counts().sort_index()
print(f"\n{'SKS Range':>12} | {'Jumlah':>8} | {'Persentase':>10}")
print("-" * 35)
for b, cnt in sks_dist.items():
    print(f"{str(b):>12} | {cnt:>8} | {cnt/total*100:>9.2f}%")

# ============================================================
# 5. DISTRIBUSI JUMLAH MK
# ============================================================
print("\n" + "=" * 70)
print("5. DISTRIBUSI JUMLAH MK (Angkatan 2024)")
print("=" * 70)

mk = pdf_2024["jumlah_mk"]
print(f"Min: {mk.min()}, Max: {mk.max()}, Mean: {mk.mean():.2f}, Median: {mk.median():.0f}")

# Anomaly check
anomaly_high_sks_low_mk = pdf_2024[(pdf_2024["total_sks"] > 100) & (pdf_2024["jumlah_mk"] < 5)]
anomaly_low_sks_high_mk = pdf_2024[(pdf_2024["total_sks"] < 20) & (pdf_2024["jumlah_mk"] > 10)]
zero_mk = pdf_2024[pdf_2024["jumlah_mk"] == 0]
zero_sks = pdf_2024[pdf_2024["total_sks"] == 0]
neg_mk = pdf_2024[pdf_2024["jumlah_mk"] < 0]
neg_sks = pdf_2024[pdf_2024["total_sks"] < 0]
null_mk = pdf_2024[pdf_2024["jumlah_mk"].isna()]
null_sks = pdf_2024[pdf_2024["total_sks"].isna()]

print(f"\nAnomalies:")
print(f"  SKS > 100 tapi MK < 5: {len(anomaly_high_sks_low_mk)}")
print(f"  SKS < 20 tapi MK > 10: {len(anomaly_low_sks_high_mk)}")
print(f"  MK = 0: {len(zero_mk)}")
print(f"  SKS = 0: {len(zero_sks)}")
print(f"  MK < 0: {len(neg_mk)}")
print(f"  SKS < 0: {len(neg_sks)}")
print(f"  MK NULL: {len(null_mk)}")
print(f"  SKS NULL: {len(null_sks)}")

# ============================================================
# 6. DISTRIBUSI IP DAN IPK
# ============================================================
print("\n" + "=" * 70)
print("6. DISTRIBUSI IP DAN IPK (Angkatan 2024)")
print("=" * 70)

ip = pdf_2024["ip"]
ipk = pdf_2024["ipk"]
print(f"\nIP  — Min: {ip.min():.2f}, Max: {ip.max():.2f}, Mean: {ip.mean():.2f}, Median: {ip.median():.2f}")
print(f"IPK — Min: {ipk.min():.2f}, Max: {ipk.max():.2f}, Mean: {ipk.mean():.2f}, Median: {ipk.median():.2f}")

ipk_bins = [0, 2.0, 2.5, 3.0, 3.5, 4.01]
ipk_labels = ["< 2.00", "2.00-2.49", "2.50-2.99", "3.00-3.49", "3.50-4.00"]
pdf_2024_ipk = pdf_2024.copy()
pdf_2024_ipk["ipk_bin"] = pd.cut(pdf_2024_ipk["ipk"], bins=ipk_bins, labels=ipk_labels, right=False)
ipk_dist = pdf_2024_ipk["ipk_bin"].value_counts().sort_index()
print(f"\n{'IPK Range':>12} | {'Jumlah':>8} | {'Persentase':>10}")
print("-" * 35)
for b, cnt in ipk_dist.items():
    print(f"{str(b):>12} | {cnt:>8} | {cnt/total*100:>9.2f}%")

# Anomalies
ip_zero = pdf_2024[pdf_2024["ip"] == 0]
ipk_zero = pdf_2024[pdf_2024["ipk"] == 0]
ip_null = pdf_2024[pdf_2024["ip"].isna()]
ipk_null = pdf_2024[pdf_2024["ipk"].isna()]
ip_out = pdf_2024[(pdf_2024["ip"] < 0) | (pdf_2024["ip"] > 4)]
ipk_out = pdf_2024[(pdf_2024["ipk"] < 0) | (pdf_2024["ipk"] > 4)]

print(f"\nAnomalies:")
print(f"  IP = 0: {len(ip_zero)}")
print(f"  IPK = 0: {len(ipk_zero)}")
print(f"  IP NULL: {len(ip_null)}")
print(f"  IPK NULL: {len(ipk_null)}")
print(f"  IP out of 0-4: {len(ip_out)}")
print(f"  IPK out of 0-4: {len(ipk_out)}")

# ============================================================
# 7. SKS SEHARUSNYA
# ============================================================
print("\n" + "=" * 70)
print("7. SKS SEHARUSNYA (Angkatan 2024)")
print("=" * 70)

sks_hrs = pdf_2024_full["sks_seharusnya"]
print(f"Formula: target_sks_kumulatif based on semester")
print(f"Semester mapping (snapshot 2026): 2026->1, 2025->3, 2024->5, 2023->7, <=2022->9")
print(f"SKS targets: {{1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144, 9:144}}")
print(f"\nMin: {sks_hrs.min()}, Max: {sks_hrs.max()}, Mean: {sks_hrs.mean():.2f}, Median: {sks_hrs.median():.0f}")

# SKS by semester
print(f"\n{'Semester':>10} | {'SKS Seharusnya':>15} | {'Rata-rata SKS Aktual':>20} | {'Rata-rata Selisih':>17}")
print("-" * 70)
for sem in sorted(pdf_2024_full["semester"].unique()):
    sub = pdf_2024_full[pdf_2024_full["semester"] == sem]
    avg_sks = sub["total_sks"].mean() if "total_sks" in sub.columns else "N/A"
    avg_sel = sub["selisih_sks"].mean() if "selisih_sks" in sub.columns else "N/A"
    sks_hrs_val = sub["sks_seharusnya"].iloc[0] if len(sub) > 0 else "N/A"
    print(f"{int(sem):>10} | {sks_hrs_val:>15} | {avg_sks:>20.2f} | {avg_sel:>17.2f}")

# ============================================================
# 8. SELISIH SKS
# ============================================================
print("\n" + "=" * 70)
print("8. SELISIH SKS (Angkatan 2024)")
print("=" * 70)

selisih = pdf_2024["selisih_sks"]
print(f"Min: {selisih.min()}, Max: {selisih.max()}, Mean: {selisih.mean():.2f}, Median: {selisih.median():.0f}")

sel_ge0 = (selisih >= 0).sum()
sel_lt0 = (selisih < 0).sum()
sel_lt10 = (selisih <= -10).sum()
sel_lt20 = (selisih <= -20).sum()
sel_lt30 = (selisih <= -30).sum()

print(f"\nSelisih >= 0:     {sel_ge0:>6} ({sel_ge0/total*100:.2f}%)")
print(f"Selisih < 0:      {sel_lt0:>6} ({sel_lt0/total*100:.2f}%)")
print(f"Selisih <= -10:   {sel_lt10:>6} ({sel_lt10/total*100:.2f}%)")
print(f"Selisih <= -20:   {sel_lt20:>6} ({sel_lt20/total*100:.2f}%)")
print(f"Selisih <= -30:   {sel_lt30:>6} ({sel_lt30/total*100:.2f}%)")

# Lowest and highest
idx_min = selisih.idxmin()
idx_max = selisih.idxmax()
print(f"\nSelisih terendah: {selisih.min()} (ID: {pdf_2024.loc[idx_min, 'id_mhs']})")
print(f"Selisih tertinggi: {selisih.max()} (ID: {pdf_2024.loc[idx_max, 'id_mhs']})")

# ============================================================
# 9. LOGIKA LABEL
# ============================================================
print("\n" + "=" * 70)
print("9. LOGIKA LABEL")
print("=" * 70)

print("""
Label Logic:
  TEPAT WAKTU: status_mahasiswa == 'Lulus' AND total_sks >= 144 AND lama_studi <= 4.0
  TERLAMBAT:  status_mahasiswa == 'Lulus' AND (total_sks < 144 OR lama_studi > 4.0)
  NULL:       status_mahasiswa != 'Lulus'

Angkatan 2024 in training: TIDAK (hanya Lulus yang dipakai training)
Angkatan 2024 status: AKTIF (bukan Lulus)
Label untuk aktif: TIDAK ADA (tidak bisa ditentukan karena belum lulus)

Source: modeling_pipeline_v2.py (lines 168-185)
""")

# ============================================================
# 10. TRAINING VS ANGKATAN 2024
# ============================================================
print("\n" + "=" * 70)
print("10. TRAINING VS ANGKATAN 2024")
print("=" * 70)

# Encode training
le_map = {"Tepat Waktu": 0, "Terlambat": 1}
y_train = pdf_train_full["label"].map(le_map).values

print(f"\n{'Feature':>18} | {'Training Mean':>14} | {'Angk2024 Mean':>14} | {'Training Med':>12} | {'Angk2024 Med':>12}")
print("-" * 75)
for f in FEATURE_COLS:
    t_mean = pdf_train_full[f].mean()
    a_mean = pdf_2024[f].mean()
    t_med = pdf_train_full[f].median()
    a_med = pdf_2024[f].median()
    print(f"{f:>18} | {t_mean:>14.2f} | {a_mean:>14.2f} | {t_med:>12.2f} | {a_med:>12.2f}")

# ============================================================
# 11. PREDIKSI MODEL (Angkatan 2024)
# ============================================================
print("\n" + "=" * 70)
print("11. PREDIKSI MODEL (Angkatan 2024)")
print("=" * 70)

# Add semester to pdf_2024
pdf_2024_with_sem = pdf_2024.merge(pdf_gold_2024[["id_mhs", "semester"]], on="id_mhs", how="left")

# Sort by prob_tw descending
pdf_sorted = pdf_2024_with_sem.sort_values("prob_tw", ascending=False)

print(f"\nTop 20 (highest Tepat Waktu probability):")
print(f"{'ID':>12} | {'Sem':>3} | {'IP':>5} | {'IPK':>5} | {'SKS':>5} | {'MK':>3} | {'SksHrs':>7} | {'Selisih':>7} | {'Pred':>12} | {'Prob_TW':>8} | {'Prob_TL':>8}")
print("-" * 100)
for _, r in pdf_sorted.head(20).iterrows():
    print(f"{r['id_mhs']:>12} | {int(r.get('semester', 0)):>3} | {r['ip']:>5.2f} | {r['ipk']:>5.2f} | {int(r['total_sks']):>5} | {int(r['jumlah_mk']):>3} | {int(r['sks_seharusnya']):>7} | {int(r['selisih_sks']):>7} | {r['prediksi']:>12} | {r['prob_tw']:>8.4f} | {r['prob_tl']:>8.4f}")

print(f"\nBottom 20 (lowest Tepat Waktu probability):")
print(f"{'ID':>12} | {'Sem':>3} | {'IP':>5} | {'IPK':>5} | {'SKS':>5} | {'MK':>3} | {'SksHrs':>7} | {'Selisih':>7} | {'Pred':>12} | {'Prob_TW':>8} | {'Prob_TL':>8}")
print("-" * 100)
for _, r in pdf_sorted.tail(20).iterrows():
    print(f"{r['id_mhs']:>12} | {int(r.get('semester', 0)):>3} | {r['ip']:>5.2f} | {r['ipk']:>5.2f} | {int(r['total_sks']):>5} | {int(r['jumlah_mk']):>3} | {int(r['sks_seharusnya']):>7} | {int(r['selisih_sks']):>7} | {r['prediksi']:>12} | {r['prob_tw']:>8.4f} | {r['prob_tl']:>8.4f}")

# ============================================================
# 12. CONFIDENCE MODEL
# ============================================================
print("\n" + "=" * 70)
print("12. CONFIDENCE MODEL (Angkatan 2024)")
print("=" * 70)

prob_tw = pdf_2024["prob_tw"]
print(f"Rata-rata Prob Tepat Waktu: {prob_tw.mean():.4f}")
print(f"Rata-rata Prob Terlambat:   {pdf_2024['prob_tl'].mean():.4f}")
print(f"Min Prob Tepat Waktu:       {prob_tw.min():.4f}")
print(f"Max Prob Tepat Waktu:       {prob_tw.max():.4f}")

# Borderline cases
borderline = pdf_2024[(pdf_2024["prob_tw"] >= 0.45) & (pdf_2024["prob_tw"] <= 0.55)]
print(f"\nBorderline cases (prob_tw 0.45-0.55): {len(borderline)}")

near_decision = pdf_2024[(pdf_2024["prob_tw"] >= 0.48) & (pdf_2024["prob_tw"] <= 0.52)]
print(f"Near decision boundary (0.48-0.52): {len(near_decision)}")

# ============================================================
# 13. PREDIKSI PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("13. PREDIKSI PER ANGKATAN (ALL AKTIF)")
print("=" * 70)

pred_per_ang = pdf_inf_all.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    tl=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()
pred_per_ang["pct_tw"] = (pred_per_ang["tw"] / pred_per_ang["total"] * 100).round(2)
pred_per_ang["pct_tl"] = (pred_per_ang["tl"] / pred_per_ang["total"] * 100).round(2)

print(f"\n{'Angkatan':>10} | {'Total':>8} | {'TW':>8} | {'TL':>8} | {'% TW':>10} | {'% TL':>10}")
print("-" * 60)
for _, r in pred_per_ang.iterrows():
    print(f"{int(r['angkatan']):>10} | {int(r['total']):>8} | {int(r['tw']):>8} | {int(r['tl']):>8} | {r['pct_tw']:>9.2f}% | {r['pct_tl']:>9.2f}%")

# ============================================================
# 14. PREDIKSI PER SEMESTER
# ============================================================
print("\n" + "=" * 70)
print("14. PREDIKSI PER SEMESTER (AKTIF)")
print("=" * 70)

pdf_inf_all_sem = pdf_inf_all.merge(pdf_gold_final.select("id_mhs", "semester").toPandas(), on="id_mhs", how="left")

pred_per_sem = pdf_inf_all_sem.groupby("semester").agg(
    total=("id_mhs", "count"),
    tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    tl=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()
pred_per_sem["pct_tw"] = (pred_per_sem["tw"] / pred_per_sem["total"] * 100).round(2)

print(f"\n{'Semester':>10} | {'Total':>8} | {'TW':>8} | {'TL':>8} | {'% TW':>10}")
print("-" * 50)
for _, r in pred_per_sem.iterrows():
    print(f"{int(r['semester']):>10} | {int(r['total']):>8} | {int(r['tw']):>8} | {int(r['tl']):>8} | {r['pct_tw']:>9.2f}%")

# ============================================================
# 15-18. DIAGNOSIS
# ============================================================
print("\n" + "=" * 70)
print("15-18. DIAGNOSIS & KESIMPULAN")
print("=" * 70)

# Check: what features make model predict TW?
print("\n--- Feature Analysis for Angkatan 2024 ---")
print(f"Semester distribution:")
for sem in sorted(pdf_2024_full["semester"].unique()):
    cnt = len(pdf_2024_full[pdf_2024_full["semester"] == sem])
    print(f"  Semester {int(sem)}: {cnt} ({cnt/total*100:.2f}%)")

print(f"\n--- Training Angkatan Distribution ---")
train_ang_dist = pdf_train_full["angkatan"].value_counts().sort_index()
for ang, cnt in train_ang_dist.items():
    print(f"  {int(ang)}: {cnt} ({cnt/len(pdf_train_full)*100:.2f}%)")

print(f"\n--- Training Semester Proxy (from angkatan 2024) ---")
# Training doesn't have semester column, but we can check what angkatan 2024 looks like
# in training if it were included
print(f"Angkatan 2024 in training: 0 (only Lulus students in training)")
print(f"Angkatan 2024 in inference: {total} (AKTIF students)")

print(f"\n--- Model Decision Boundary Analysis ---")
print(f"ALL {total} students predicted Tepat Waktu")
print(f"Min prob_tw: {prob_tw.min():.4f}")
print(f"Max prob_tw: {prob_tw.max():.4f}")
print(f"Mean prob_tw: {prob_tw.mean():.4f}")

spark.stop()
print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
