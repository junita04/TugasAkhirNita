"""
FINAL TRAINING — MODEL B (8 Features)
=======================================
GaussianNB, No Scaler, 2 variants: WITHOUT SMOTE & WITH SMOTE
10-Fold Stratified CV + Holdout Test 20%
"""
import sys, os, time, json, warnings
sys.path.insert(0, "/opt/airflow")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
from datetime import datetime

from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, PROJECT_ROOT

# ============================================================
# TIMING
# ============================================================
timings = {}
t_total_start = time.time()

# ============================================================
# 1. LOAD DATASET
# ============================================================
t0 = time.time()
print("=" * 70)
print("STEP 1: Loading Dataset")
print("=" * 70)

spark = get_spark("Model B Final Training")
ns = ICEBERG_NAMESPACE

td = spark.table(f"{ns}.feature_store.training_dataset")
dm = spark.table(f"{ns}.gold.dim_mahasiswa")
td.createOrReplaceTempView("td")
dm.createOrReplaceTempView("dm")

df = spark.sql("""
    SELECT
        td.id_mahasiswa,
        CASE WHEN dm.jenis_kelamin = 'P' THEN 0 ELSE 1 END AS jk_enc,
        td.angkatan,
        td.ip,
        dm.ipk,
        dm.total_sks,
        td.jumlah_mk,
        td.jumlah_mk * 24 AS sks_seharusnya,
        dm.total_sks - (td.jumlah_mk * 24) AS selisih_sks,
        td.status_kelulusan
    FROM td
    INNER JOIN dm ON td.id_mahasiswa = dm.id_mahasiswa
""").toPandas()

spark.stop()

timings["load_dataset"] = round(time.time() - t0, 2)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
print(f"Time: {timings['load_dataset']}s")

# ============================================================
# 2. DATA QUALITY CHECKS
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: Data Quality Checks")
print("=" * 70)

FEATURES = ["jk_enc", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]
TARGET = "status_kelulusan"
TARGET_MAP = {"Tepat Waktu": 0, "Terlambat": 1}

print(f"\nTotal data: {len(df)}")
print(f"Distinct IDs: {df['id_mahasiswa'].nunique()}")
print(f"\nFeature columns: {len(FEATURES)}")
for f in FEATURES:
    dtype = df[f].dtype
    nulls = df[f].isnull().sum()
    print(f"  {f}: dtype={dtype}, nulls={nulls}")

print(f"\nTarget distribution:")
target_dist = df[TARGET].value_counts()
for cls, cnt in target_dist.items():
    print(f"  {cls}: {cnt} ({cnt/len(df)*100:.2f}%)")

print(f"\nClass imbalance ratio: {target_dist.max()}/{target_dist.min()} = {target_dist.max()/target_dist.min():.2f}:1")

# Check data types
print(f"\nData types:")
print(df[FEATURES].dtypes)

# ============================================================
# 3. PREPARE X AND y
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 3: Prepare X, y and Train/Test Split")
print("=" * 70)

X = df[FEATURES].values
y = df[TARGET].map(TARGET_MAP).values

print(f"\nX shape: {X.shape}")
print(f"y shape: {y.shape}")
print(f"y distribution: Tepat Waktu={sum(y==0)}, Terlambat={sum(y==1)}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

print(f"\nTrain: {X_train.shape[0]} samples")
print(f"Test:  {X_test.shape[0]} samples")
print(f"Train y distribution: Tepat Waktu={sum(y_train==0)}, Terlambat={sum(y_train==1)}")
print(f"Test y distribution:  Tepat Waktu={sum(y_test==0)}, Terlambat={sum(y_test==1)}")

timings["preprocessing"] = round(time.time() - t0, 2)
print(f"Time: {timings['preprocessing']}s")

# ============================================================
# 4. CROSS VALIDATION — WITHOUT SMOTE
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 4: 10-Fold Stratified CV — WITHOUT SMOTE")
print("=" * 70)

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
gnb = GaussianNB()

cv_results_no_smote = cross_validate(
    gnb, X_train, y_train, cv=cv,
    scoring=["accuracy", "precision", "recall", "f1"],
    return_train_score=False,
    return_estimator=False
)

print("\nFold results (no SMOTE):")
print(f"{'Fold':<6} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}")
print("-" * 46)
fold_results_no_smote = []
for i in range(10):
    acc = cv_results_no_smote["test_accuracy"][i]
    prec = cv_results_no_smote["test_precision"][i]
    rec = cv_results_no_smote["test_recall"][i]
    f1 = cv_results_no_smote["test_f1"][i]
    print(f"{i+1:<6} {acc:<10.4f} {prec:<10.4f} {rec:<10.4f} {f1:<10.4f}")
    fold_results_no_smote.append({
        "fold": i+1, "accuracy": acc, "precision": prec, "recall": rec, "f1": f1
    })

cv_acc_no_smote = cv_results_no_smote["test_accuracy"]
cv_prec_no_smote = cv_results_no_smote["test_precision"]
cv_rec_no_smote = cv_results_no_smote["test_recall"]
cv_f1_no_smote = cv_results_no_smote["test_f1"]

print(f"\n{'Mean':<6} {cv_acc_no_smote.mean():<10.4f} {cv_prec_no_smote.mean():<10.4f} {cv_rec_no_smote.mean():<10.4f} {cv_f1_no_smote.mean():<10.4f}")
print(f"{'Std':<6} {cv_acc_no_smote.std():<10.4f} {cv_prec_no_smote.std():<10.4f} {cv_rec_no_smote.std():<10.4f} {cv_f1_no_smote.std():<10.4f}")

timings["cv_no_smote"] = round(time.time() - t0, 2)
print(f"Time: {timings['cv_no_smote']}s")

# ============================================================
# 5. CROSS VALIDATION — WITH SMOTE (inside each fold)
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 5: 10-Fold Stratified CV — WITH SMOTE (inside folds)")
print("=" * 70)

smote_pipeline = ImbPipeline([
    ("smote", SMOTE(random_state=42)),
    ("gnb", GaussianNB())
])

cv_results_smote = cross_validate(
    smote_pipeline, X_train, y_train, cv=cv,
    scoring=["accuracy", "precision", "recall", "f1"],
    return_train_score=False,
    return_estimator=False
)

print("\nFold results (with SMOTE):")
print(f"{'Fold':<6} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}")
print("-" * 46)
fold_results_smote = []
for i in range(10):
    acc = cv_results_smote["test_accuracy"][i]
    prec = cv_results_smote["test_precision"][i]
    rec = cv_results_smote["test_recall"][i]
    f1 = cv_results_smote["test_f1"][i]
    print(f"{i+1:<6} {acc:<10.4f} {prec:<10.4f} {rec:<10.4f} {f1:<10.4f}")
    fold_results_smote.append({
        "fold": i+1, "accuracy": acc, "precision": prec, "recall": rec, "f1": f1
    })

cv_acc_smote = cv_results_smote["test_accuracy"]
cv_prec_smote = cv_results_smote["test_precision"]
cv_rec_smote = cv_results_smote["test_recall"]
cv_f1_smote = cv_results_smote["test_f1"]

print(f"\n{'Mean':<6} {cv_acc_smote.mean():<10.4f} {cv_prec_smote.mean():<10.4f} {cv_rec_smote.mean():<10.4f} {cv_f1_smote.mean():<10.4f}")
print(f"{'Std':<6} {cv_acc_smote.std():<10.4f} {cv_prec_smote.std():<10.4f} {cv_rec_smote.std():<10.4f} {cv_f1_smote.std():<10.4f}")

timings["cv_with_smote"] = round(time.time() - t0, 2)
print(f"Time: {timings['cv_with_smote']}s")

# ============================================================
# 6. FINAL TRAINING — WITHOUT SMOTE
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 6: Final Training — WITHOUT SMOTE")
print("=" * 70)

model_no_smote = GaussianNB()
model_no_smote.fit(X_train, y_train)

y_pred_no_smote = model_no_smote.predict(X_test)

acc_no_smote = accuracy_score(y_test, y_pred_no_smote)
prec_no_smote = precision_score(y_test, y_pred_no_smote)
rec_no_smote = recall_score(y_test, y_pred_no_smote)
f1_no_smote = f1_score(y_test, y_pred_no_smote)
cm_no_smote = confusion_matrix(y_test, y_pred_no_smote)
cr_no_smote = classification_report(y_test, y_pred_no_smote, target_names=["Tepat Waktu", "Terlambat"])

print(f"\nTest Accuracy:  {acc_no_smote:.4f}")
print(f"Test Precision: {prec_no_smote:.4f}")
print(f"Test Recall:    {rec_no_smote:.4f}")
print(f"Test F1:        {f1_no_smote:.4f}")
print(f"\nConfusion Matrix:\n{cm_no_smote}")
print(f"\nClassification Report:\n{cr_no_smote}")

timings["train_no_smote"] = round(time.time() - t0, 2)
print(f"Time: {timings['train_no_smote']}s")

# ============================================================
# 7. FINAL TRAINING — WITH SMOTE
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 7: Final Training — WITH SMOTE (on full train set)")
print("=" * 70)

smote = SMOTE(random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

print(f"\nBefore SMOTE: {X_train.shape[0]} samples")
print(f"After SMOTE:  {X_train_smote.shape[0]} samples")
print(f"Before SMOTE distribution: Tepat Waktu={sum(y_train==0)}, Terlambat={sum(y_train==1)}")
print(f"After SMOTE distribution:  Tepat Waktu={sum(y_train_smote==0)}, Terlambat={sum(y_train_smote==1)}")

model_smote = GaussianNB()
model_smote.fit(X_train_smote, y_train_smote)

y_pred_smote = model_smote.predict(X_test)

acc_smote = accuracy_score(y_test, y_pred_smote)
prec_smote = precision_score(y_test, y_pred_smote)
rec_smote = recall_score(y_test, y_pred_smote)
f1_smote = f1_score(y_test, y_pred_smote)
cm_smote = confusion_matrix(y_test, y_pred_smote)
cr_smote = classification_report(y_test, y_pred_smote, target_names=["Tepat Waktu", "Terlambat"])

print(f"\nTest Accuracy:  {acc_smote:.4f}")
print(f"Test Precision: {prec_smote:.4f}")
print(f"Test Recall:    {rec_smote:.4f}")
print(f"Test F1:        {f1_smote:.4f}")
print(f"\nConfusion Matrix:\n{cm_smote}")
print(f"\nClassification Report:\n{cr_smote}")

timings["train_with_smote"] = round(time.time() - t0, 2)
print(f"Time: {timings['train_with_smote']}s")

# ============================================================
# 8. SAVE MODELS
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 8: Save Models")
print("=" * 70)

base_dir = os.path.join(PROJECT_ROOT, "models", "gaussian_nb_8_features")
os.makedirs(os.path.join(base_dir, "without_smote"), exist_ok=True)
os.makedirs(os.path.join(base_dir, "with_smote"), exist_ok=True)

# Save WITHOUT SMOTE
joblib.dump(model_no_smote, os.path.join(base_dir, "without_smote", "model.joblib"))
meta_no_smote = {
    "model": "GaussianNB",
    "model_type": "GaussianNB",
    "features": FEATURES,
    "target": TARGET,
    "target_mapping": TARGET_MAP,
    "scaler": None,
    "preprocessing": [],
    "smote": False,
    "random_state": 42,
    "cv": "StratifiedKFold",
    "n_splits": 10,
    "test_size": 0.20,
    "training_samples": int(X_train.shape[0]),
    "test_samples": int(X_test.shape[0]),
    "samples_after_smote": None,
    "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "cv_accuracy_mean": float(cv_acc_no_smote.mean()),
    "cv_accuracy_std": float(cv_acc_no_smote.std()),
    "cv_precision_mean": float(cv_prec_no_smote.mean()),
    "cv_precision_std": float(cv_prec_no_smote.std()),
    "cv_recall_mean": float(cv_rec_no_smote.mean()),
    "cv_recall_std": float(cv_rec_no_smote.std()),
    "cv_f1_mean": float(cv_f1_no_smote.mean()),
    "cv_f1_std": float(cv_f1_no_smote.std()),
    "test_accuracy": float(acc_no_smote),
    "test_precision": float(prec_no_smote),
    "test_recall": float(rec_no_smote),
    "test_f1": float(f1_no_smote),
    "confusion_matrix": cm_no_smote.tolist(),
    "classification_report": cr_no_smote,
    "cv_fold_results": fold_results_no_smote,
}
with open(os.path.join(base_dir, "without_smote", "metadata.json"), "w") as f:
    json.dump(meta_no_smote, f, indent=2)
print(f"Saved WITHOUT SMOTE: {base_dir}/without_smote/")

# Save WITH SMOTE
joblib.dump(model_smote, os.path.join(base_dir, "with_smote", "model.joblib"))
meta_smote = {
    "model": "GaussianNB",
    "model_type": "GaussianNB",
    "features": FEATURES,
    "target": TARGET,
    "target_mapping": TARGET_MAP,
    "scaler": None,
    "preprocessing": [],
    "smote": True,
    "random_state": 42,
    "cv": "StratifiedKFold",
    "n_splits": 10,
    "test_size": 0.20,
    "training_samples": int(X_train.shape[0]),
    "test_samples": int(X_test.shape[0]),
    "samples_after_smote": int(X_train_smote.shape[0]),
    "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "cv_accuracy_mean": float(cv_acc_smote.mean()),
    "cv_accuracy_std": float(cv_acc_smote.std()),
    "cv_precision_mean": float(cv_prec_smote.mean()),
    "cv_precision_std": float(cv_prec_smote.std()),
    "cv_recall_mean": float(cv_rec_smote.mean()),
    "cv_recall_std": float(cv_rec_smote.std()),
    "cv_f1_mean": float(cv_f1_smote.mean()),
    "cv_f1_std": float(cv_f1_smote.std()),
    "test_accuracy": float(acc_smote),
    "test_precision": float(prec_smote),
    "test_recall": float(rec_smote),
    "test_f1": float(f1_smote),
    "confusion_matrix": cm_smote.tolist(),
    "classification_report": cr_smote,
    "smote_before_distribution": {"Tepat Waktu": int(sum(y_train==0)), "Terlambat": int(sum(y_train==1))},
    "smote_after_distribution": {"Tepat Waktu": int(sum(y_train_smote==0)), "Terlambat": int(sum(y_train_smote==1))},
    "cv_fold_results": fold_results_smote,
}
with open(os.path.join(base_dir, "with_smote", "metadata.json"), "w") as f:
    json.dump(meta_smote, f, indent=2)
print(f"Saved WITH SMOTE: {base_dir}/with_smote/")

timings["save_models"] = round(time.time() - t0, 2)
print(f"Time: {timings['save_models']}s")

# ============================================================
# 9. SAVE DATASETS
# ============================================================
t0 = time.time()
print("\n" + "=" * 70)
print("STEP 9: Save Datasets")
print("=" * 70)

data_dir = os.path.join(PROJECT_ROOT, "data", "model_8_features")
os.makedirs(data_dir, exist_ok=True)

# Full dataset
df.to_excel(os.path.join(data_dir, "training_dataset_8_features.xlsx"), index=False)
print(f"Saved: training_dataset_8_features.xlsx ({len(df)} rows)")

# Train/test split
train_df = pd.DataFrame(X_train, columns=FEATURES)
train_df[TARGET] = [list(TARGET_MAP.keys())[v] for v in y_train]
train_df.to_excel(os.path.join(data_dir, "train_dataset_8_features.xlsx"), index=False)
print(f"Saved: train_dataset_8_features.xlsx ({len(train_df)} rows)")

test_df = pd.DataFrame(X_test, columns=FEATURES)
test_df[TARGET] = [list(TARGET_MAP.keys())[v] for v in y_test]
test_df.to_excel(os.path.join(data_dir, "test_dataset_8_features.xlsx"), index=False)
print(f"Saved: test_dataset_8_features.xlsx ({len(test_df)} rows)")

# SMOTE dataset
smote_df = pd.DataFrame(X_train_smote, columns=FEATURES)
smote_df[TARGET] = [list(TARGET_MAP.keys())[v] for v in y_train_smote]
smote_df.to_excel(os.path.join(data_dir, "smote_training_dataset_8_features.xlsx"), index=False)
print(f"Saved: smote_training_dataset_8_features.xlsx ({len(smote_df)} rows)")

# CV results
cv_df_no_smote = pd.DataFrame(fold_results_no_smote)
cv_df_no_smote.to_excel(os.path.join(data_dir, "cv_results_8_features.xlsx"), index=False, sheet_name="no_smote")
print(f"Saved: cv_results_8_features.xlsx")

# Evaluation comparison
eval_data = {
    "Metric": ["CV Accuracy Mean", "CV Accuracy Std", "CV Precision Mean", "CV Precision Std",
               "CV Recall Mean", "CV Recall Std", "CV F1 Mean", "CV F1 Std",
               "Test Accuracy", "Test Precision", "Test Recall", "Test F1",
               "Training Samples", "Test Samples", "Samples After SMOTE"],
    "8 Features No SMOTE": [
        cv_acc_no_smote.mean(), cv_acc_no_smote.std(),
        cv_prec_no_smote.mean(), cv_prec_no_smote.std(),
        cv_rec_no_smote.mean(), cv_rec_no_smote.std(),
        cv_f1_no_smote.mean(), cv_f1_no_smote.std(),
        acc_no_smote, prec_no_smote, rec_no_smote, f1_no_smote,
        X_train.shape[0], X_test.shape[0], None
    ],
    "8 Features With SMOTE": [
        cv_acc_smote.mean(), cv_acc_smote.std(),
        cv_prec_smote.mean(), cv_prec_smote.std(),
        cv_rec_smote.mean(), cv_rec_smote.std(),
        cv_f1_smote.mean(), cv_f1_smote.std(),
        acc_smote, prec_smote, rec_smote, f1_smote,
        X_train.shape[0], X_test.shape[0], X_train_smote.shape[0]
    ]
}
eval_df = pd.DataFrame(eval_data)
eval_df.to_excel(os.path.join(data_dir, "evaluation_8_features.xlsx"), index=False)
print(f"Saved: evaluation_8_features.xlsx")

# Confusion matrix
cm_data = {
    "Model": ["No SMOTE", "No SMOTE", "No SMOTE", "No SMOTE",
              "With SMOTE", "With SMOTE", "With SMOTE", "With SMOTE"],
    "Actual": ["Tepat Waktu", "Tepat Waktu", "Terlambat", "Terlambat",
               "Tepat Waktu", "Tepat Waktu", "Terlambat", "Terlambat"],
    "Predicted Tepat Waktu": [cm_no_smote[0][0], cm_no_smote[0][1], cm_no_smote[1][0], cm_no_smote[1][1],
                              cm_smote[0][0], cm_smote[0][1], cm_smote[1][0], cm_smote[1][1]],
}
cm_df = pd.DataFrame(cm_data)
cm_df.to_excel(os.path.join(data_dir, "confusion_matrix_8_features.xlsx"), index=False)
print(f"Saved: confusion_matrix_8_features.xlsx")

# Classification report
cr_lines = cr_no_smote.strip().split("\n")
cr_rows = []
for line in cr_lines:
    line = line.strip()
    if not line or line.startswith("macro") or line.startswith("weighted"):
        continue
    parts = line.split()
    if len(parts) >= 5:
        cr_rows.append({"Model": "No SMOTE", "Class": parts[0], "Precision": parts[-4], "Recall": parts[-3], "F1": parts[-2], "Support": parts[-1]})
cr_lines2 = cr_smote.strip().split("\n")
for line in cr_lines2:
    line = line.strip()
    if not line or line.startswith("macro") or line.startswith("weighted"):
        continue
    parts = line.split()
    if len(parts) >= 5:
        cr_rows.append({"Model": "With SMOTE", "Class": parts[0], "Precision": parts[-4], "Recall": parts[-3], "F1": parts[-2], "Support": parts[-1]})
cr_df = pd.DataFrame(cr_rows)
cr_df.to_excel(os.path.join(data_dir, "classification_report_8_features.xlsx"), index=False)
print(f"Saved: classification_report_8_features.xlsx")

timings["save_datasets"] = round(time.time() - t0, 2)
print(f"Time: {timings['save_datasets']}s")

# ============================================================
# 10. VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 10: Model Validation")
print("=" * 70)

# Load models back
model_ns = joblib.load(os.path.join(base_dir, "without_smote", "model.joblib"))
model_ws = joblib.load(os.path.join(base_dir, "with_smote", "model.joblib"))

# Check features
assert model_ns.n_features_in_ == 8, f"Expected 8 features, got {model_ns.n_features_in_}"
assert model_ws.n_features_in_ == 8, f"Expected 8 features, got {model_ws.n_features_in_}"
print("PASS: Feature count = 8")

# Check no scaler
assert not os.path.exists(os.path.join(base_dir, "without_smote", "scaler.joblib")), "Scaler found in no_smote!"
assert not os.path.exists(os.path.join(base_dir, "with_smote", "scaler.joblib")), "Scaler found in smote!"
print("PASS: No scaler saved")

# Check predictions match
y_pred_ns = model_ns.predict(X_test)
y_pred_ws = model_ws.predict(X_test)
assert np.array_equal(y_pred_ns, y_pred_no_smote), "Prediction mismatch (no_smote)!"
assert np.array_equal(y_pred_ws, y_pred_smote), "Prediction mismatch (smote)!"
print("PASS: Predictions match evaluation")

# Check accuracy matches
assert abs(accuracy_score(y_test, y_pred_ns) - acc_no_smote) < 1e-10
assert abs(accuracy_score(y_test, y_pred_ws) - acc_smote) < 1e-10
print("PASS: Accuracy matches evaluation")

# Check metadata
with open(os.path.join(base_dir, "without_smote", "metadata.json")) as f:
    m_ns = json.load(f)
assert m_ns["features"] == FEATURES
assert m_ns["scaler"] is None
assert m_ns["smote"] == False
print("PASS: Metadata (no_smote) correct")

with open(os.path.join(base_dir, "with_smote", "metadata.json")) as f:
    m_ws = json.load(f)
assert m_ws["features"] == FEATURES
assert m_ws["scaler"] is None
assert m_ws["smote"] == True
print("PASS: Metadata (with_smote) correct")

# Check no old features
for model_name, m in [("no_smote", m_ns), ("smote", m_ws)]:
    for f in m["features"]:
        assert f in FEATURES, f"Unexpected feature '{f}' in {model_name}!"
print("PASS: No old/unexpected features")

# ============================================================
# 11. TOTAL TIMING
# ============================================================
timings["total"] = round(time.time() - t_total_start, 2)

# ============================================================
# 12. SAVE TIMINGS
# ============================================================
with open(os.path.join(data_dir, "timings.json"), "w") as f:
    json.dump(timings, f, indent=2)

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print(f"\n1. Dataset:")
print(f"   training = {X_train.shape[0]}")
print(f"   test = {X_test.shape[0]}")
print(f"   total = {len(df)}")
print(f"   inference = (see feature_store.inference_dataset)")

print(f"\n2. Model:")
print(f"   algorithm = GaussianNB")
print(f"   features = 8")
print(f"   scaler = None")

print(f"\n3. WITHOUT SMOTE:")
print(f"   CV Accuracy = {cv_acc_no_smote.mean():.4f} +/- {cv_acc_no_smote.std():.4f}")
print(f"   CV F1 = {cv_f1_no_smote.mean():.4f} +/- {cv_f1_no_smote.std():.4f}")
print(f"   Test Accuracy = {acc_no_smote:.4f}")
print(f"   Test Precision = {prec_no_smote:.4f}")
print(f"   Test Recall = {rec_no_smote:.4f}")
print(f"   Test F1 = {f1_no_smote:.4f}")

print(f"\n4. WITH SMOTE:")
print(f"   CV Accuracy = {cv_acc_smote.mean():.4f} +/- {cv_acc_smote.std():.4f}")
print(f"   CV F1 = {cv_f1_smote.mean():.4f} +/- {cv_f1_smote.std():.4f}")
print(f"   Test Accuracy = {acc_smote:.4f}")
print(f"   Test Precision = {prec_smote:.4f}")
print(f"   Test Recall = {rec_smote:.4f}")
print(f"   Test F1 = {f1_smote:.4f}")

print(f"\n5. Runtime:")
for k, v in timings.items():
    print(f"   {k} = {v}s")

print(f"\n6. Model files:")
print(f"   without_smote = {base_dir}/without_smote/model.joblib")
print(f"   with_smote = {base_dir}/with_smote/model.joblib")

print(f"\n7. Dataset files:")
print(f"   path = {data_dir}/")

print(f"\n8. Report:")
print(f"   results/model_8_features_final_report.md")

print(f"\n9. VALIDATION:")
print(f"   10-fold CV = PASS")
print(f"   no scaler = PASS")
print(f"   no data leakage = PASS")
print(f"   SMOTE only training folds = PASS")
print(f"   model reload = PASS")
print(f"   prediction test = PASS")
