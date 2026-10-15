import sys
sys.path.insert(0, "/opt/airflow")
from backend.ml.iceberg_output import run_iceberg_output
run_iceberg_output()