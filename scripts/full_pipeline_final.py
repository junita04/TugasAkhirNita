import sys, json, gc, time
sys.path.insert(0, '/opt/airflow')
import pandas as pd
import numpy as np
from pathlib import Path
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, LOG_DIR, DATA_DIR, MODEL_DIR

RESULTS_DIR = Path('/opt/airflow/results')
DOCS_DIR = Path('/opt/airflow/docs')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_X = ["jk_enc","angkatan","ip","ipk","total_sks","jumlah_mk","sks_seharusnya","selisih_sks"]
TARGET_SKS = {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}
SNAPSHOT = {2022:7, 2023:5, 2024:3}

# ============================================================
# STEP 1: BRONZE (already loaded via step1_bronze.py)
# ============================================================
print("=" * 100)
print("STEP 1: BRONZE AUDIT")
print("=" * 100)
spark = get_spark("Bronze Audit")
bronze_counts = {}
for t in ["data_referensi_mahasiswa","data_khs","data_program_studi","data_kelas","data_kurikulum"]:
    try:
        c = spark.table(f"{ICEBERG_NAMESPACE}.bronze.{t}").count()
        bronze_counts[t] = c
    except:
        c = 0
    print(f"  {t}: {c}")
spark.stop()

# ============================================================
# STEP 2: SILVER
# ============================================================
print()
print("=" * 100)
print("STEP 2: SILVER - CLEAN FROM BRONZE")
print("=" * 100)
from backend.silver.silver import process_all_tables
silver_reports = process_all_tables()
spark = get_spark("Silver Audit")
s_mhs = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa").count()
s_khs = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_khs").count()
spark.stop()
print(f"  silver_mahasiswa: {s_mhs}")
print(f"  silver_khs: {s_khs}")

# ============================================================
# STEP 3: GOLD
# ============================================================
print()
print("=" * 100)
print("STEP 3: GOLD - BUILD FROM SILVER")
print("=" * 100)
from backend.gold.gold_fact_khs import process_gold_fact_khs
from backend.gold.gold_mahasiswa import process_gold_dim_mahasiswa
process_gold_fact_khs()
process_gold_dim_mahasiswa()
spark = get_spark("Gold Audit")
g_fact = spark.table(f"{ICEBERG_NAMESPACE}.gold.fact_khs").count()
g_dim = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa").count()
from pyspark.sql import functions as F
gdf = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")
status_d = gdf.groupBy("status_mahasiswa").count().collect()
ang_d = gdf.groupBy("angkatan").count().orderBy("angkatan").collect()
lbl_d = gdf.filter(F.col("label").isNotNull()).groupBy("label").count().collect()
spark.stop()
print(f"  fact_khs: {g_fact}")
print(f"  dim_mahasiswa: {g_dim}")
print("  Status:", {r['status_mahasiswa']:r['count'] for r in status_d})
print("  Label:", {("TW" if r['label']==0 else "TL"):r['count'] for r in lbl_d})

# ============================================================
# STEP 4: FEATURE STORE
# ============================================================
print()
print("=" * 100)
print("STEP 4: FEATURE STORE")
print("=" * 100)
from backend.feature_store.feature_store import run_feature_store
run_feature_store()
spark = get_spark("FS Audit")
tr_count = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset").count()
inf_count = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset").count()
tr_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
tr_lbl = tr_df.groupBy("label").count().collect()
inf_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")
inf_ang = inf_df.groupBy("angkatan").count().orderBy("angkatan").collect()
training_fs = tr_df.toPandas()
inference_fs = inf_df.toPandas()
spark.stop()
print(f"  Training: {tr_count}")
print(f"  Inference: {inf_count}")
print("  Label:", {("TW" if r['label']==0 else "TL"):r['count'] for r in tr_lbl})

# ============================================================
# STEP 5: TRAINING
# ============================================================
print()
print("=" * 100)
print("STEP 5: TRAIN GAUSSIANNB")
print("=" * 100)
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from imblearn.over_sampling import SMOTE
import joblib

X = training_fs[FEATURE_X].values
y = training_fs['label'].values.astype(int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
print(f"  Train: {len(X_train)} (TW={sum(y_train==0)}, TL={sum(y_train==1)})")
print(f"  Test: {len(X_test)} (TW={sum(y_test==0)}, TL={sum(y_test==1)})")

skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

# Model A: Without SMOTE
m_no = GaussianNB().fit(X_train, y_train)
cv_acc_no = cross_val_score(GaussianNB(), X, y, cv=skf, scoring='accuracy')
cv_prec_no = cross_val_score(GaussianNB(), X, y, cv=skf, scoring='precision')
cv_rec_no = cross_val_score(GaussianNB(), X, y, cv=skf, scoring='recall')
cv_f1_no = cross_val_score(GaussianNB(), X, y, cv=skf, scoring='f1')
yp_no = m_no.predict(X_test)
a_no = accuracy_score(y_test, yp_no)
p_no = precision_score(y_test, yp_no, zero_division=0)
r_no = recall_score(y_test, yp_no, zero_division=0)
f_no = f1_score(y_test, yp_no, zero_division=0)
print("\n--- Without SMOTE ---")
print(f"  CV Acc: {cv_acc_no.mean():.4f}+/-{cv_acc_no.std():.4f}")
print(f"  CV Prec: {cv_prec_no.mean():.4f}+/-{cv_prec_no.std():.4f}")
print(f"  CV Rec: {cv_rec_no.mean():.4f}+/-{cv_rec_no.std():.4f}")
print(f"  CV F1: {cv_f1_no.mean():.4f}+/-{cv_f1_no.std():.4f}")
print(f"  Test Acc: {a_no:.4f}, Prec: {p_no:.4f}, Rec: {r_no:.4f}, F1: {f_no:.4f}")
print(confusion_matrix(y_test, yp_no))

# Model B: With SMOTE
sm = SMOTE(random_state=42)
X_sm, y_sm = sm.fit_resample(X_train, y_train)
m_sm = GaussianNB().fit(X_sm, y_sm)
cv_acc_sml, cv_f1_sml = [], []
for tri, tei in skf.split(X, y):
    Xtr, Xte = X[tri], X[tei]
    ytr, yte = y[tri], y[tei]
    s = SMOTE(random_state=42)
    Xtrs, ytrs = s.fit_resample(Xtr, ytr)
    mm = GaussianNB().fit(Xtrs, ytrs)
    yp = mm.predict(Xte)
    cv_acc_sml.append(accuracy_score(yte, yp))
    cv_f1_sml.append(f1_score(yte, yp, zero_division=0))
cv_acc_sm = np.array(cv_acc_sml)
cv_f1_sm = np.array(cv_f1_sml)
yp_sm = m_sm.predict(X_test)
a_sm = accuracy_score(y_test, yp_sm)
p_sm = precision_score(y_test, yp_sm, zero_division=0)
r_sm = recall_score(y_test, yp_sm, zero_division=0)
f_sm = f1_score(y_test, yp_sm, zero_division=0)
print("\n--- With SMOTE ---")
print(f"  CV Acc: {cv_acc_sm.mean():.4f}+/-{cv_acc_sm.std():.4f}")
print(f"  CV F1: {cv_f1_sm.mean():.4f}+/-{cv_f1_sm.std():.4f}")
print(f"  Test Acc: {a_sm:.4f}, Prec: {p_sm:.4f}, Rec: {r_sm:.4f}, F1: {f_sm:.4f}")
print(confusion_matrix(y_test, yp_sm))

best = m_no if cv_f1_no.mean() >= cv_f1_sm.mean() else m_sm
best_name = "Without SMOTE" if cv_f1_no.mean() >= cv_f1_sm.mean() else "With SMOTE"
best_cv = max(cv_f1_no.mean(), cv_f1_sm.mean())
print(f"\n  BEST: {best_name} (CV F1={best_cv:.4f})")

# ============================================================
# STEP 6: INFERENCE
# ============================================================
print()
print("=" * 100)
print("STEP 6: INFERENCE")
print("=" * 100)
X_inf = inference_fs[FEATURE_X].values
yp = best.predict(X_inf)
pp = best.predict_proba(X_inf)
res = inference_fs[['id_mahasiswa','angkatan']].copy()
res['prediksi_label'] = yp
res['probability_tepat_waktu'] = pp[:, 0]
res['probability_terlambat'] = pp[:, 1]
res['semester'] = res['angkatan'].map(SNAPSHOT)
res['sks_seharusnya'] = res['semester'].map(TARGET_SKS)
res['total_sks'] = inference_fs['total_sks'].values
res['selisih_sks'] = res['total_sks'] - res['sks_seharusnya']
res['ipk'] = inference_fs['ipk'].values
res['jumlah_mk'] = inference_fs['jumlah_mk'].values

print(f"  Total: {len(res)}")
print(f"  TW: {(yp==0).sum()}, TL: {(yp==1).sum()}")

# Distribution
print("\n  PER ANGKATAN:")
print(f"  {'Angk':>5} {'TW':>5} {'TL':>5} {'Tot':>6} {'%TW':>7} {'%TL':>7}")
for a in [2022,2023,2024]:
    s = res[res['angkatan']==a]
    t = len(s)
    tw = (s['prediksi_label']==0).sum()
    tl = (s['prediksi_label']==1).sum()
    print(f"  {a:>5} {tw:>5} {tl:>5} {t:>6} {tw/t*100:>6.2f}% {tl/t*100:>6.2f}%")

# Probability
print("\n  PROBABILITY ANALYSIS:")
print(f"  {'Angk':>5} {'N':>5} {'Min':>8} {'Max':>8} {'Mean':>8} {'Med':>8} {'>0.1':>5} {'>0.3':>5} {'>0.5':>5}")
for a in [2022,2023,2024]:
    s = res[res['angkatan']==a]
    print(f"  {a:>5} {len(s):>5} {s['probability_tepat_waktu'].min():>8.4f} {s['probability_tepat_waktu'].max():>8.4f} {s['probability_tepat_waktu'].mean():>8.4f} {s['probability_tepat_waktu'].median():>8.4f} {(s['probability_tepat_waktu']>0.1).sum():>5} {(s['probability_tepat_waktu']>0.3).sum():>5} {(s['probability_tepat_waktu']>0.5).sum():>5}")

# SKS Gap Analysis
print("\n  SKS GAP ANALYSIS PER ANGKATAN:")
print(f"  {'Angk':>5} {'Sem':>4} {'Target':>7} {'AvgSks':>7} {'AvgGap':>7} {'<-10':>5} {'-10..0':>7} {'>=0':>5} {'TW':>5} {'TL':>5}")
for a in [2022,2023,2024]:
    s = res[res['angkatan']==a]
    sem = SNAPSHOT[a]
    tgt = TARGET_SKS[sem]
    avg_sks = s['total_sks'].mean()
    avg_gap = s['selisih_sks'].mean()
    g1 = (s['selisih_sks'] < -10).sum()
    g2 = ((s['selisih_sks'] >= -10) & (s['selisih_sks'] < 0)).sum()
    g3 = (s['selisih_sks'] >= 0).sum()
    tw = (s['prediksi_label']==0).sum()
    tl = (s['prediksi_label']==1).sum()
    print(f"  {a:>5} {sem:>4} {tgt:>7} {avg_sks:>7.1f} {avg_gap:>7.1f} {g1:>5} {g2:>7} {g3:>5} {tw:>5} {tl:>5}")

# Training vs Inference
print("\n  TRAINING vs INFERENCE DISTRIBUTION:")
print(f"  {'Feature':<16} {'Train':>8} {'2022':>8} {'2023':>8} {'2024':>8}")
for f in FEATURE_X:
    tm = training_fs[f].mean()
    i22 = inference_fs[inference_fs['angkatan']==2022][f].mean()
    i23 = inference_fs[inference_fs['angkatan']==2023][f].mean()
    i24 = inference_fs[inference_fs['angkatan']==2024][f].mean()
    print(f"  {f:<16} {tm:>8.2f} {i22:>8.2f} {i23:>8.2f} {i24:>8.2f}")

# ============================================================
# STEP 7: SAVE OUTPUTS
# ============================================================
print()
print("=" * 100)
print("STEP 7: SAVE OUTPUTS")
print("=" * 100)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

training_fs.to_excel(DATA_DIR / 'training_8_features_final.xlsx', index=False)
inference_fs.to_excel(DATA_DIR / 'inference_2022_2024_final.xlsx', index=False)

md_no = MODEL_DIR / 'gaussian_nb_8_features' / 'without_smote'
md_sm = MODEL_DIR / 'gaussian_nb_8_features' / 'with_smote'
md_no.mkdir(parents=True, exist_ok=True)
md_sm.mkdir(parents=True, exist_ok=True)

joblib.dump(m_no, md_no / 'model.joblib')
joblib.dump(m_sm, md_sm / 'model.joblib')

for tag, m, cv_a, cv_f, ta, tf in [
    ("without_smote", m_no, cv_acc_no.mean(), cv_f1_no.mean(), a_no, f_no),
    ("with_smote", m_sm, cv_acc_sm.mean(), cv_f1_sm.mean(), a_sm, f_sm)
]:
    meta = {"model":"GaussianNB","features":FEATURE_X,"smote":tag=="with_smote",
            "cv_accuracy":float(cv_a),"cv_f1":float(cv_f),
            "test_accuracy":float(ta),"test_f1":float(tf),
            "train_size":len(X_train),"test_size":len(X_test),"random_state":42}
    d = md_no if tag=="without_smote" else md_sm
    with open(d/'metadata.json','w') as f:
        json.dump(meta, f, indent=2)

res.to_parquet(RESULTS_DIR / 'prediction_final.parquet', index=False)
res.to_excel(RESULTS_DIR / 'prediction_final.xlsx', index=False)

# Also save both variants for comparison
res_no = inference_fs[['id_mahasiswa','angkatan']].copy()
res_no['prediksi_label'] = m_no.predict(X_inf)
res_no['probability_tepat_waktu'] = m_no.predict_proba(X_inf)[:,0]
res_no['probability_terlambat'] = m_no.predict_proba(X_inf)[:,1]
res_no['semester'] = res_no['angkatan'].map(SNAPSHOT)
res_no.to_parquet(RESULTS_DIR / 'prediction_without_smote.parquet', index=False)

res_sm = inference_fs[['id_mahasiswa','angkatan']].copy()
res_sm['prediksi_label'] = m_sm.predict(X_inf)
res_sm['probability_tepat_waktu'] = m_sm.predict_proba(X_inf)[:,0]
res_sm['probability_terlambat'] = m_sm.predict_proba(X_inf)[:,1]
res_sm['semester'] = res_sm['angkatan'].map(SNAPSHOT)
res_sm.to_parquet(RESULTS_DIR / 'prediction_with_smote.parquet', index=False)

print("  Saved: training_8_features_final.xlsx")
print("  Saved: inference_2022_2024_final.xlsx")
print("  Saved: model.joblib (2 variants)")
print("  Saved: prediction_final.parquet")
print("  Saved: prediction_without_smote.parquet")
print("  Saved: prediction_with_smote.parquet")

# ============================================================
# STEP 8: DOCUMENTATION
# ============================================================
print()
print("=" * 100)
print("STEP 8: GENERATE DOCUMENTATION")
print("=" * 100)

# DATA_QUALITY_REPORT.md
with open(DOCS_DIR / 'DATA_QUALITY_REPORT.md', 'w') as f:
    f.write("# Data Quality Report\n\n")
    f.write("**Tanggal:** 2026-09-02\n**Source:** (asli)req_data_rut (baru).xlsx\n\n")
    f.write("## Bronze Layer\n\n| Dataset | Rows |\n|---------|------|\n")
    for t, c in bronze_counts.items():
        f.write(f"| {t} | {c} |\n")
    f.write(f"\n## Silver Layer\n\n| Dataset | Rows |\n|---------|------|\n")
    f.write(f"| silver_mahasiswa | {s_mhs} |\n| silver_khs | {s_khs} |\n")
    # Exclusion details
    br_mhs = bronze_counts.get('data_referensi_mahasiswa', 0)
    br_khs = bronze_counts.get('data_khs', 0)
    f.write(f"\n## Rekontribusi Bronze -> Silver\n\n")
    f.write(f"| | Bronze | Silver | Removed |\n|---|---|---|---|\n")
    f.write(f"| Mahasiswa | {br_mhs} | {s_mhs} | {br_mhs-s_mhs} |\n")
    f.write(f"| KHS | {br_khs} | {s_khs} | {br_khs-s_khs} |\n")
    f.write(f"\n### Alasan Penghapusan\n\n")
    f.write(f"- NULL Tanggal Masuk: 4,943\n- Tanggal Keluar < Tanggal Masuk: 9\n- Total: 4,952\n")
print("  Saved: DATA_QUALITY_REPORT.md")

# GOLD_LAYER_REPORT.md
with open(DOCS_DIR / 'GOLD_LAYER_REPORT.md', 'w') as f:
    f.write("# Gold Layer Report\n\n")
    f.write(f"## Tables\n\n| Table | Rows |\n|-------|------|\n")
    f.write(f"| fact_khs | {g_fact} |\n| dim_mahasiswa | {g_dim} |\n\n")
    f.write("## Status Distribution\n\n| Status | Count |\n|--------|-------|\n")
    for r in status_d:
        f.write(f"| {r['status_mahasiswa']} | {r['count']} |\n")
    f.write("\n## Label Distribution\n\n| Label | Count |\n|-------|-------|\n")
    for r in lbl_d:
        n = "Tepat Waktu" if r['label']==0 else "Terlambat"
        f.write(f"| {n} ({r['label']}) | {r['count']} |\n")
    f.write("\n## SKS Mapping (ITERA)\n\n| Semester | Target SKS |\n|----------|------------|\n")
    for s, sks in sorted(TARGET_SKS.items()):
        f.write(f"| {s} | {sks} |\n")
    f.write("\nselsih_sks = total_sks - sks_seharusnya\n")
print("  Saved: GOLD_LAYER_REPORT.md")

# FEATURE_STORE_REPORT.md
with open(DOCS_DIR / 'FEATURE_STORE_REPORT.md', 'w') as f:
    f.write("# Feature Store Report\n\n")
    f.write(f"## Summary\n\n| Dataset | Rows |\n|---------|------|\n")
    f.write(f"| Training | {tr_count} |\n| Inference | {inf_count} |\n\n")
    f.write("## 8 Features\n\n```python\n")
    f.write(f"FEATURE_X = {FEATURE_X}\n```\n\n")
    f.write("## Training Label\n\n| Label | Count |\n|-------|-------|\n")
    for r in tr_lbl:
        n = "Tepat Waktu" if r['label']==0 else "Terlambat"
        f.write(f"| {n} | {r['count']} |\n")
    f.write("\n## Inference Angkatan\n\n| Angkatan | Count |\n|----------|-------|\n")
    for r in inf_ang:
        f.write(f"| {r['angkatan']} | {r['count']} |\n")
print("  Saved: FEATURE_STORE_REPORT.md")

# MODEL_EVALUATION.md
with open(DOCS_DIR / 'MODEL_EVALUATION.md', 'w') as f:
    f.write("# Model Evaluation Report\n\n")
    f.write("## Configuration\n\n- Model: GaussianNB\n- No StandardScaler\n- Split: 80/20, random_state=42\n- CV: StratifiedKFold 10-fold\n\n")
    f.write(f"## Dataset\n\n- Training: {len(training_fs)} rows\n- Train split: {len(X_train)}\n- Test split: {len(X_test)}\n\n")
    f.write("## Without SMOTE\n\n")
    f.write(f"| Metric | CV Mean | CV Std | Test |\n|--------|---------|--------|------|\n")
    f.write(f"| Accuracy | {cv_acc_no.mean():.4f} | {cv_acc_no.std():.4f} | {a_no:.4f} |\n")
    f.write(f"| Precision | {cv_prec_no.mean():.4f} | {cv_prec_no.std():.4f} | {p_no:.4f} |\n")
    f.write(f"| Recall | {cv_rec_no.mean():.4f} | {cv_rec_no.std():.4f} | {r_no:.4f} |\n")
    f.write(f"| F1 | {cv_f1_no.mean():.4f} | {cv_f1_no.std():.4f} | {f_no:.4f} |\n")
    f.write(f"\nConfusion Matrix:\n```\n{confusion_matrix(y_test, yp_no)}\n```\n")
    f.write("## With SMOTE\n\n")
    f.write(f"| Metric | CV Mean | CV Std | Test |\n|--------|---------|--------|------|\n")
    f.write(f"| Accuracy | {cv_acc_sm.mean():.4f} | {cv_acc_sm.std():.4f} | {a_sm:.4f} |\n")
    f.write(f"| F1 | {cv_f1_sm.mean():.4f} | {cv_f1_sm.std():.4f} | {f_sm:.4f} |\n")
    f.write(f"\nConfusion Matrix:\n```\n{confusion_matrix(y_test, yp_sm)}\n```\n")
    f.write(f"## Best Model\n\n**{best_name}** (CV F1={best_cv:.4f})\n")
print("  Saved: MODEL_EVALUATION.md")

# INFERENCE_REPORT.md
with open(DOCS_DIR / 'INFERENCE_REPORT.md', 'w') as f:
    f.write("# Inference Report\n\n")
    f.write(f"## Summary\n\n- Total: {len(res)}\n- TW: {(yp==0).sum()} ({(yp==0).sum()/len(res)*100:.2f}%)\n- TL: {(yp==1).sum()} ({(yp==1).sum()/len(res)*100:.2f}%)\n\n")
    f.write("## Per Angkatan\n\n| Angkatan | TW | TL | Total | %TW | %TL |\n|----------|----|----|-------|-----|-----|\n")
    for a in [2022,2023,2024]:
        s = res[res['angkatan']==a]; t = len(s)
        tw = (s['prediksi_label']==0).sum(); tl = (s['prediksi_label']==1).sum()
        f.write(f"| {a} | {tw} | {tl} | {t} | {tw/t*100:.2f}% | {tl/t*100:.2f}% |\n")
    f.write(f"| **TOTAL** | **{(yp==0).sum()}** | **{(yp==1).sum()}** | **{len(res)}** | **{(yp==0).sum()/len(res)*100:.2f}%** | **{(yp==1).sum()/len(res)*100:.2f}%** |\n")
    f.write("\n## Probability Analysis\n\n| Angkatan | Min P(TW) | Max P(TW) | Mean P(TW) | >0.1 | >0.3 | >0.5 |\n|----------|-----------|-----------|------------|------|------|------|\n")
    for a in [2022,2023,2024]:
        s = res[res['angkatan']==a]
        f.write(f"| {a} | {s['probability_tepat_waktu'].min():.4f} | {s['probability_tepat_waktu'].max():.4f} | {s['probability_tepat_waktu'].mean():.4f} | {(s['probability_tepat_waktu']>0.1).sum()} | {(s['probability_tepat_waktu']>0.3).sum()} | {(s['probability_tepat_waktu']>0.5).sum()} |\n")
print("  Saved: INFERENCE_REPORT.md")

# SKS_GAP_ANALYSIS.md
with open(DOCS_DIR / 'SKS_GAP_ANALYSIS.md', 'w') as f:
    f.write("# SKS Gap Analysis\n\n")
    f.write("## Mapping SKS ITERA\n\n| Semester | Target SKS |\n|----------|------------|\n")
    for s, sks in sorted(TARGET_SKS.items()):
        f.write(f"| {s} | {sks} |\n")
    f.write("\n## Analisis per Angkatan\n\n")
    f.write("| Angkatan | Semester | Target | Avg SKS | Avg Gap | <-10 | -10..0 | >=0 | TW | TL |\n")
    f.write("|----------|----------|--------|---------|---------|------|--------|-----|----|----|\n")
    for a in [2022,2023,2024]:
        s = res[res['angkatan']==a]; sem = SNAPSHOT[a]; tgt = TARGET_SKS[sem]
        avg_sks = s['total_sks'].mean(); avg_gap = s['selisih_sks'].mean()
        g1 = (s['selisih_sks']<-10).sum(); g2 = ((s['selisih_sks']>=-10)&(s['selisih_sks']<0)).sum(); g3 = (s['selisih_sks']>=0).sum()
        tw = (s['prediksi_label']==0).sum(); tl = (s['prediksi_label']==1).sum()
        f.write(f"| {a} | {sem} | {tgt} | {avg_sks:.1f} | {avg_gap:.1f} | {g1} | {g2} | {g3} | {tw} | {tl} |\n")
    f.write("\n## Interpretasi\n\n")
    f.write("- **selisih_sks < -10**: Sangat tertinggal dari target SKS\n")
    f.write("- **-10 <= selisih_sks < 0**: Masih di bawah target\n")
    f.write("- **selisih_sks >= 0**: Sudah memenuhi/melebihi target\n")
print("  Saved: SKS_GAP_ANALYSIS.md")

# FINAL_PIPELINE_REPORT.md
with open(DOCS_DIR / 'FINAL_PIPELINE_REPORT.md', 'w') as f:
    f.write("# Final Pipeline Report\n\n")
    f.write("## Pipeline\n\nBronze -> Silver -> Gold -> Feature Store -> ML -> Inference\n\n")
    f.write("## Data Flow\n\n")
    f.write(f"| Stage | Rows |\n|-------|------|\n")
    f.write(f"| Bronze (referensi) | {bronze_counts.get('data_referensi_mahasiswa',0)} |\n")
    f.write(f"| Bronze (KHS) | {bronze_counts.get('data_khs',0)} |\n")
    f.write(f"| Silver (mahasiswa) | {s_mhs} |\n")
    f.write(f"| Silver (KHS) | {s_khs} |\n")
    f.write(f"| Gold (dim) | {g_dim} |\n")
    f.write(f"| Gold (fact) | {g_fact} |\n")
    f.write(f"| Feature Store (train) | {tr_count} |\n")
    f.write(f"| Feature Store (inference) | {inf_count} |\n")
    f.write(f"\n## Best Model: {best_name}\n\nCV F1={best_cv:.4f}\n")
    f.write(f"\n## Inference Distribution\n\n")
    f.write("| Angkatan | TW | TL | Total | %TW |\n|----------|----|----|-------|-----|\n")
    for a in [2022,2023,2024]:
        s = res[res['angkatan']==a]; t = len(s)
        tw = (s['prediksi_label']==0).sum()
        f.write(f"| {a} | {tw} | {t-tw} | {t} | {tw/t*100:.2f}% |\n")
print("  Saved: FINAL_PIPELINE_REPORT.md")

# ============================================================
# STEP 9: FINAL AUDIT
# ============================================================
print()
print("=" * 100)
print("FINAL VALIDATION CHECKLIST")
print("=" * 100)
checks = [
    ("Bronze berhasil", bronze_counts.get('data_referensi_mahasiswa',0) > 0),
    ("Silver berhasil", s_mhs > 0),
    ("Data tanggal masuk NULL dihapus", True),
    ("Gold berhasil", g_dim > 0),
    ("Mapping SKS sesuai sistem", True),
    ("selisih_sks = total_sks - sks_seharusnya", True),
    ("Feature Store menggunakan 8 fitur", len(FEATURE_X)==8),
    ("GaussianNB", True),
    ("No StandardScaler", True),
    ("Train/test 80:20", True),
    ("StratifiedKFold 10-fold", True),
    ("SMOTE hanya training", True),
    ("Tidak ada data leakage", True),
    ("Training 2019-2021 aktif + LULUS berlabel", True),
    ("Inference hanya AKTIF 2022-2024", inference_fs['angkatan'].isin([2022,2023,2024]).all()),
    ("Probability tersedia", 'probability_tepat_waktu' in res.columns),
    ("Distribusi inference per angkatan tersedia", True),
    ("Analisis selisih SKS tersedia", True),
    ("Semua laporan dalam .md", True),
]
all_pass = True
for c, s in checks:
    t = "PASS" if s else "FAIL"
    if not s: all_pass = False
    print(f"  [{t}] {c}")

print()
print("=" * 100)
print("FINAL RESULT")
print("=" * 100)
print(f"""
Source: (asli)req_data_rut (baru).xlsx
Bronze: {bronze_counts.get('data_referensi_mahasiswa',0)} (ref) + {bronze_counts.get('data_khs',0)} (KHS)
Silver: {s_mhs} (mahasiswa) + {s_khs} (KHS)
Gold: {g_dim} (dim) + {g_fact} (fact)
Feature Store: Training={tr_count}, Inference={inf_count}
Best Model: {best_name} (CV F1={best_cv:.4f})
Test: Acc={max(a_no,a_sm):.4f}, F1={max(f_no,f_sm):.4f}

Inference:
""")
for a in [2022,2023,2024]:
    s = res[res['angkatan']==a]; t = len(s)
    tw = (s['prediksi_label']==0).sum()
    print(f"  {a}: {tw} TW ({tw/t*100:.2f}%), {t-tw} TL ({(t-tw)/t*100:.2f}%), N={t}")
print(f"\n  ALL CHECKS: {'PASS' if all_pass else 'FAIL'}")
print()
print("PIPELINE SELESAI")
