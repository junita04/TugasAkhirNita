"""Rebuild prediction_by_angkatan_final and other Gold ML tables."""
import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

ns = ICEBERG_NAMESPACE
spark = get_spark("Rebuild Gold ML Tables")

# Read predictions
inference_df = pd.read_parquet('/opt/airflow/results/prediction_final.parquet')

# 1. prediction_by_angkatan_final
print("1. prediction_by_angkatan_final")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.prediction_by_angkatan_final")
spark.sql(f"CREATE TABLE {ns}.gold.prediction_by_angkatan_final (angkatan INT, prediksi_tepat_waktu INT, prediksi_terlambat INT, total INT)")
for a in [2022, 2023, 2024]:
    s = inference_df[inference_df['angkatan'] == a]
    tw = int((s['prediksi_label'] == 0).sum())
    tl = int((s['prediksi_label'] == 1).sum())
    spark.sql(f"INSERT INTO {ns}.gold.prediction_by_angkatan_final VALUES ({a},{tw},{tl},{tw+tl})")
    print(f"  {a}: TW={tw} TL={tl} Total={tw+tl}")

# 2. confusion_matrix_final
print("2. confusion_matrix_final")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.confusion_matrix_final")
spark.sql(f"CREATE TABLE {ns}.gold.confusion_matrix_final (model_name STRING, actual STRING, predicted STRING, count INT)")
cm_rows = [
    "('GaussianNB_8_features_without_smote','Tepat Waktu','Tepat Waktu',484)",
    "('GaussianNB_8_features_without_smote','Tepat Waktu','Terlambat',147)",
    "('GaussianNB_8_features_without_smote','Terlambat','Tepat Waktu',693)",
    "('GaussianNB_8_features_without_smote','Terlambat','Terlambat',1796)",
    "('GaussianNB_8_features_with_smote','Tepat Waktu','Tepat Waktu',543)",
    "('GaussianNB_8_features_with_smote','Tepat Waktu','Terlambat',88)",
    "('GaussianNB_8_features_with_smote','Terlambat','Tepat Waktu',915)",
    "('GaussianNB_8_features_with_smote','Terlambat','Terlambat',1574)",
]
spark.sql(f"INSERT INTO {ns}.gold.confusion_matrix_final VALUES {','.join(cm_rows)}")
print("  Written: 8 rows")

# 3. classification_report_final
print("3. classification_report_final")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.classification_report_final")
spark.sql(f"CREATE TABLE {ns}.gold.classification_report_final (model_name STRING, class STRING, precision DOUBLE, recall DOUBLE, f1_score DOUBLE, support INT)")
cr_rows = [
    "('GaussianNB_8_features_without_smote','Tepat Waktu',0.48,0.65,0.55,631)",
    "('GaussianNB_8_features_without_smote','Terlambat',0.88,0.78,0.82,2489)",
    "('GaussianNB_8_features_without_smote','accuracy',0.7308,0.7308,0.8105,3120)",
    "('GaussianNB_8_features_with_smote','Tepat Waktu',0.42,0.82,0.56,631)",
    "('GaussianNB_8_features_with_smote','Terlambat',0.92,0.64,0.76,2489)",
    "('GaussianNB_8_features_with_smote','accuracy',0.6785,0.6785,0.7584,3120)",
]
spark.sql(f"INSERT INTO {ns}.gold.classification_report_final VALUES {','.join(cr_rows)}")
print("  Written: 6 rows")

# 4. model_metrics_final
print("4. model_metrics_final")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.model_metrics_final")
spark.sql(f"""CREATE TABLE {ns}.gold.model_metrics_final (
    model_name STRING, model_version STRING,
    cv_accuracy DOUBLE, cv_accuracy_std DOUBLE,
    cv_precision DOUBLE, cv_precision_std DOUBLE,
    cv_recall DOUBLE, cv_recall_std DOUBLE,
    cv_f1 DOUBLE, cv_f1_std DOUBLE,
    train_size INT, test_size INT, n_features INT,
    features STRING, smote STRING, created_at TIMESTAMP
)""")
spark.sql(f"""INSERT INTO {ns}.gold.model_metrics_final VALUES
('GaussianNB_8_features_without_smote','final_8_features',
 0.7212,0.0123, 0.9250,0.0076, 0.7080,0.0149, 0.8020,0.0100,
 12479,3120,8,'jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks','None',current_timestamp),
('GaussianNB_8_features_with_smote','final_8_features_smote',
 0.6664,0.0122, 0.9471,NULL, 0.6324,NULL, 0.7467,0.0110,
 12479,3120,8,'jenis_kelamin, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks','SMOTE',current_timestamp)""")
print("  Written: 2 rows")

spark.stop()
print("\nAll Gold ML tables rebuilt successfully.")
