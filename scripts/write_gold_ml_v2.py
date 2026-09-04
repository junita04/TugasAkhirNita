"""Write ML results to Gold schema tables using Spark directly."""
import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd
import numpy as np
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from imblearn.over_sampling import SMOTE
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

FEATURE_X = ["jk_enc","angkatan","ip","ipk","total_sks","jumlah_mk","sks_seharusnya","selisih_sks"]

# Load data
training_df = pd.read_excel('/opt/airflow/data/training_8_features_final.xlsx')
inference_df = pd.read_parquet('/opt/airflow/results/prediction_final.parquet')

X = training_df[FEATURE_X].values
y = training_df['label'].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train models
gnb_no = GaussianNB()
gnb_no.fit(X_train, y_train)
y_pred_no = gnb_no.predict(X_test)

skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
cv_no = cross_validate(gnb_no, X, y, cv=skf, scoring=['accuracy','precision','recall','f1'])

smote = SMOTE(random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
gnb_sm = GaussianNB()
gnb_sm.fit(X_train_sm, y_train_sm)
y_pred_sm = gnb_sm.predict(X_test)
cv_sm = cross_validate(gnb_sm, X_train_sm, y_train_sm, cv=skf, scoring=['accuracy','precision','recall','f1'])

spark = get_spark("Write Gold ML")

def drop_and_create(table, schema_sql):
    spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.gold.{table}")
    spark.sql(f"CREATE TABLE {ICEBERG_NAMESPACE}.gold.{table} ({schema_sql})")
    print(f"  Created: {table}")

# 1. model_metrics_final
print("1. model_metrics_final")
drop_and_create("model_metrics_final", """
    model_name STRING, model_version STRING,
    cv_accuracy DOUBLE, cv_accuracy_std DOUBLE,
    cv_precision DOUBLE, cv_precision_std DOUBLE,
    cv_recall DOUBLE, cv_recall_std DOUBLE,
    cv_f1 DOUBLE, cv_f1_std DOUBLE,
    train_size INT, test_size INT, n_features INT,
    features STRING, smote STRING, created_at TIMESTAMP
""")
rows = [
    f"('GaussianNB_8_features_without_smote','final_8_features',{cv_no['test_accuracy'].mean()},{cv_no['test_accuracy'].std()},{cv_no['test_precision'].mean()},{cv_no['test_precision'].std()},{cv_no['test_recall'].mean()},{cv_no['test_recall'].std()},{cv_no['test_f1'].mean()},{cv_no['test_f1'].std()},{len(X_train)},{len(X_test)},8,'jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks','None',current_timestamp)",
    f"('GaussianNB_8_features_with_smote','final_8_features_smote',{cv_sm['test_accuracy'].mean()},{cv_sm['test_accuracy'].std()},{cv_sm['test_precision'].mean()},{cv_sm['test_precision'].std()},{cv_sm['test_recall'].mean()},{cv_sm['test_recall'].std()},{cv_sm['test_f1'].mean()},{cv_sm['test_f1'].std()},{len(X_train_sm)},{len(X_test)},8,'jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks','SMOTE',current_timestamp)",
]
spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.model_metrics_final VALUES {','.join(rows)}")
print(f"  Written: 2 rows")

# 2. confusion_matrix_final
print("2. confusion_matrix_final")
drop_and_create("confusion_matrix_final", "model_name STRING, actual STRING, predicted STRING, count INT")
cm_no = confusion_matrix(y_test, y_pred_no, labels=[0, 1])
cm_sm = confusion_matrix(y_test, y_pred_sm, labels=[0, 1])
cm_rows = []
for model_name, cm in [('GaussianNB_8_features_without_smote', cm_no), ('GaussianNB_8_features_with_smote', cm_sm)]:
    for i, actual in enumerate(['Tepat Waktu', 'Terlambat']):
        for j, predicted in enumerate(['Tepat Waktu', 'Terlambat']):
            cm_rows.append(f"('{model_name}','{actual}','{predicted}',{int(cm[i][j])})")
spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.confusion_matrix_final VALUES {','.join(cm_rows)}")
print(f"  Written: {len(cm_rows)} rows")

# 3. classification_report_final
print("3. classification_report_final")
drop_and_create("classification_report_final", "model_name STRING, class STRING, precision DOUBLE, recall DOUBLE, f1_score DOUBLE, support INT")
cr_rows = []
for model_name, y_pred in [('GaussianNB_8_features_without_smote', y_pred_no), ('GaussianNB_8_features_with_smote', y_pred_sm)]:
    cr = classification_report(y_test, y_pred, target_names=['Tepat Waktu', 'Terlambat'], output_dict=True)
    for cls in ['Tepat Waktu', 'Terlambat']:
        cr_rows.append(f"('{model_name}','{cls}',{cr[cls]['precision']},{cr[cls]['recall']},{cr[cls]['f1-score']},{int(cr[cls]['support'])})")
    cr_rows.append(f"('{model_name}','accuracy',{cr['accuracy']},{cr['accuracy']},{cr['accuracy']},{int(cr['weighted avg']['support'])})")
spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.classification_report_final VALUES {','.join(cr_rows)}")
print(f"  Written: {len(cr_rows)} rows")

# 4. prediction_by_angkatan_final
print("4. prediction_by_angkatan_final")
drop_and_create("prediction_by_angkatan_final", "angkatan INT, prediksi_tepat_waktu INT, prediksi_terlambat INT, total INT")
pa_rows = []
for a in [2022, 2023, 2024]:
    s = inference_df[inference_df['angkatan'] == a]
    tw = int((s['prediksi_label'] == 0).sum())
    tl = int((s['prediksi_label'] == 1).sum())
    pa_rows.append(f"({a},{tw},{tl},{tw+tl})")
spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.prediction_by_angkatan_final VALUES {','.join(pa_rows)}")
print(f"  Written: {len(pa_rows)} rows")

# 5. model_predictions (per-student, batched)
print("5. model_predictions")
drop_and_create("model_predictions", "id_mahasiswa STRING, angkatan INT, prediksi STRING, probability DOUBLE")
batch_size = 2000
total = len(inference_df)
for start in range(0, total, batch_size):
    batch = inference_df.iloc[start:start+batch_size]
    mp_rows = []
    for _, r in batch.iterrows():
        pred = 'Tepat Waktu' if r['prediksi_label'] == 0 else 'Terlambat'
        mp_rows.append(f"('{r['id_mahasiswa']}',{r['angkatan']},'{pred}',{r['probability_tepat_waktu']})")
    spark.sql(f"INSERT INTO {ICEBERG_NAMESPACE}.gold.model_predictions VALUES {','.join(mp_rows)}")
    print(f"  Batch {start}-{min(start+batch_size, total)} done")
print(f"  Written: {total} rows")

spark.stop()
print("\nAll Gold ML tables written successfully.")
