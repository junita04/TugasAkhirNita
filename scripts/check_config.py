import sys
sys.path.insert(0, "/opt/airflow")
from backend.config.settings import ICEBERG_CATALOG, ICEBERG_WAREHOUSE, SPARK_MODE, ICEBERG_NAMESPACE
print(f"CATALOG={ICEBERG_CATALOG}")
print(f"WAREHOUSE={ICEBERG_WAREHOUSE}")
print(f"SPARK_MODE={SPARK_MODE}")
print(f"NAMESPACE={ICEBERG_NAMESPACE}")
