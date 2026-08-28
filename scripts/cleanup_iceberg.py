"""Drop old gold ML tables and old feature_store tables."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark

spark = get_spark("TugasAkhirNita - Cleanup")

tables_to_drop = [
    "iceberg.gold.model_metrics",
    "iceberg.gold.confusion_matrix",
    "iceberg.gold.classification_report",
    "iceberg.gold.model_predictions",
    "iceberg.gold.prediction_by_angkatan",
    "iceberg.feature_store.feature_store_graduation_prediction",
]

for table in tables_to_drop:
    try:
        spark.sql(f"DROP TABLE IF EXISTS {table}")
        print(f"DROPPED: {table}")
    except Exception as e:
        print(f"FAILED to drop {table}: {e}")

print("\nCleanup done.")
