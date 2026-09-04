"""Write ML results to Gold schema tables for Superset dashboard."""
import sys
sys.path.insert(0, '/opt/airflow')
import json
import numpy as np
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

# Re-run ML to get metrics (same as full_pipeline_final.py)
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from imblearn.over_sampling import SMOTE
import pandas as pd

FEATURE_X = ["jk_enc","angkatan","ip","ipk","total_sks","jumlah_mk","sks_seharusnya","selisih_sks"]

spark = get_spark("Write Gold ML Tables")

# Read training data from Excel
training_df = pd.read_excel('/opt/airflow/data/training_8_features_final.xlsx')
X = training_df[FEATURE_X].values
y = training_df['label'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Without SMOTE
gnb_no = GaussianNB()
gnb_no.fit(X_train, y_train)
y_pred_no = gnb_no.predict(X_test)

skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
cv_no = cross_validate(gnb_no, X, y, cv=skf, scoring=['accuracy','precision','recall','f1'])

# With SMOTE
smote = SMOTE(random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
gnb_sm = GaussianNB()
gnb_sm.fit(X_train_sm, y_train_sm)
y_pred_sm = gnb_sm.predict(X_test)

cv_sm = cross_validate(gnb_sm, X_train_sm, y_train_sm, cv=skf, scoring=['accuracy','precision','recall','f1'])

# Read inference data from parquet (contains predictions)
inference_df = pd.read_parquet('/opt/airflow/results/prediction_final.parquet')
# best model already fitted above

# ============================================================
# 1. model_metrics_final
# ============================================================
print("Writing gold.model_metrics_final ...")
spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.model_metrics_final")
spark.sql(f"""
CREATE TABLE {ICEBERG_NAMESPACE}.gold.model_metrics_final (
    model_name STRING,
    model_version STRING,
    cv_accuracy DOUBLE,
    cv_accuracy_std DOUBLE,
    cv_precision DOUBLE,
    cv_precision_std DOUBLE,
    cv_recall DOUBLE,
    cv_recall_std DOUBLE,
    cv_f1 DOUBLE,
    cv_f1_std DOUBLE,
    train_size INT,
    test_size INT,
    n_features INT,
    features STRING,
    smote STRING,
    created_at TIMESTAMP
)""")
spark.sql(f"""
INSERT INTO {ICEBERG_NAMESPACE}.gold.model_metrics_final VALUES
('GaussianNB_8_features_without_smote', 'final_8_features',
 {cv_no['test_accuracy'].mean()}, {cv_no['test_accuracy'].std()},
 {cv_no['test_precision'].mean()}, {cv_no['test_precision'].std()},
 {cv_no['test_recall'].mean()}, {cv_no['test_recall'].std()},
 {cv_no['test_f1'].mean()}, {cv_no['test_f1'].std()},
 {len(X_train)}, {len(X_test)}, 8,
 'jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks',
 'None', current_timestamp)
""")
spark.sql(f"""
INSERT INTO {ICEBERG_NAMESPACE}.gold.model_metrics_final VALUES
('GaussianNB_8_features_with_smote', 'final_8_features_smote',
 {cv_sm['test_accuracy'].mean()}, {cv_sm['test_accuracy'].std()},
 {cv_sm['test_precision'].mean()}, {cv_sm['test_precision'].std()},
 {cv_sm['test_recall'].mean()}, {cv_sm['test_recall'].std()},
 {cv_sm['test_f1'].mean()}, {cv_sm['test_f1'].std()},
 {len(X_train_sm)}, {len(X_test)}, 8,
 'jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks',
 'SMOTE', current_timestamp)
""")
print("  Written: gold.model_metrics_final")

# ============================================================
# 2. confusion_matrix_final
# ============================================================
print("Writing gold.confusion_matrix_final ...")
spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.confusion_matrix_final")
spark.sql(f"""
CREATE TABLE {ICEBERG_NAMESPACE}.gold.confusion_matrix_final (
    model_name STRING,
    actual STRING,
    predicted STRING,
    count INT
)""")

cm_no = confusion_matrix(y_test, y_pred_no, labels=[0, 1])
cm_sm = confusion_matrix(y_test, y_pred_sm, labels=[0, 1])

for model_name, cm in [('GaussianNB_8_features_without_smote', cm_no), ('GaussianNB_8_features_with_smote', cm_sm)]:
    for i, actual in enumerate(['Tepat Waktu', 'Terlambat']):
        for j, predicted in enumerate(['Tepat Waktu', 'Terlambat']):
            spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.confusion_matrix_final VALUES ('{model_name}', '{actual}', '{predicted}', {int(cm[i][j])})")

print("  Written: gold.confusion_matrix_final")

# ============================================================
# 3. classification_report_final
# ============================================================
print("Writing gold.classification_report_final ...")
spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.classification_report_final")
spark.sql(f"""
CREATE TABLE {ICEBERG_NAMESPACE}.gold.classification_report_final (
    model_name STRING,
    class STRING,
    precision DOUBLE,
    recall DOUBLE,
    f1_score DOUBLE,
    support INT
)""")

for model_name, y_pred in [('GaussianNB_8_features_without_smote', y_pred_no), ('GaussianNB_8_features_with_smote', y_pred_sm)]:
    cr = classification_report(y_test, y_pred, target_names=['Tepat Waktu', 'Terlambat'], output_dict=True)
    for cls in ['Tepat Waktu', 'Terlambat']:
        spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.classification_report_final VALUES ('{model_name}', '{cls}', {cr[cls]['precision']}, {cr[cls]['recall']}, {cr[cls]['f1-score']}, {int(cr[cls]['support'])})")
    spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.classification_report_final VALUES ('{model_name}', 'accuracy', {cr['accuracy']}, {cr['accuracy']}, {cr['accuracy']}, {int(cr['weighted avg']['support'])})")

print("  Written: gold.classification_report_final")

# ============================================================
# 4. prediction_by_angkatan_final
# ============================================================
print("Writing gold.prediction_by_angkatan_final ...")
spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.prediction_by_angkatan_final")
spark.sql(f"""
CREATE TABLE {ICEBERG_NAMESPACE}.gold.prediction_by_angkatan_final (
    angkatan INT,
    prediksi_tepat_waktu INT,
    prediksi_terlambat INT,
    total INT
)""")

for a in [2022, 2023, 2024]:
    s = inference_df[inference_df['angkatan'] == a]
    tw = int((s['prediksi_label'] == 0).sum())
    tl = int((s['prediksi_label'] == 1).sum())
    spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.prediction_by_angkatan_final VALUES ({a}, {tw}, {tl}, {tw + tl})")

print("  Written: gold.prediction_by_angkatan_final")

# ============================================================
# 5. model_predictions (per-student predictions)
# ============================================================
print("Writing gold.model_predictions ...")
spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.model_predictions")
spark.sql(f"""
CREATE TABLE {ICEBERG_NAMESPACE}.gold.model_predictions (
    id_mahasiswa STRING,
    angkatan INT,
    prediksi STRING,
    probability DOUBLE
)""")

inf_preds = inference_df[['id_mahasiswa','angkatan']].copy()
inf_preds['prediksi'] = ['Tepat Waktu' if p == 0 else 'Terlambat' for p in inference_df['prediksi_label']]
inf_preds['probability'] = inference_df['probability_tepat_waktu'].tolist()

# Write in batches
for start in range(0, len(inf_preds), 1000):
    batch = inf_preds.iloc[start:start+1000]
    rows = []
    for _, r in batch.iterrows():
        rows.append(f"('{r['id_mahasiswa']}', {r['angkatan']}, '{r['prediksi']}', {r['probability']})")
    values = ",".join(rows)
    spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.model_predictions VALUES {values}")

print("  Written: gold.model_predictions")

spark.stop()
print("\nAll Gold ML tables written successfully.")
