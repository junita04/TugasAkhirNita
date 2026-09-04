"""Register Iceberg tables in HMS for Trino visibility."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Register Tables for Trino")

tables = [
    ("feature_store", "prediction_result_without_smote"),
    ("feature_store", "prediction_result_with_smote"),
    ("feature_store", "prediction_comparison"),
    ("feature_store", "training_dataset"),
    ("feature_store", "inference_dataset"),
    ("gold", "dim_mahasiswa"),
    ("gold", "fact_khs"),
]

for schema, table in tables:
    full_table = f"{ICEBERG_NAMESPACE}.{schema}.{table}"
    path = f"s3a://warehouse/iceberg/{schema}/{table}"
    
    try:
        spark.sql(
            f"CALL iceberg.system.register_table("
            f"'{full_table}', '{path}')"
        )
        print(f"  OK: {full_table}")
    except Exception as e:
        print(f"  ERROR: {full_table}: {str(e)[:400]}")

print("REGISTRATION DONE")
