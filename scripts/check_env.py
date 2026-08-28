import sys, os
sys.path.insert(0, "/opt/airflow")

print("=== ENV VARS ===")
for k in ["SPARK_MODE", "ICEBERG_CATALOG", "ICEBERG_WAREHOUSE", "S3_ENDPOINT"]:
    print(f"  {k} = {os.environ.get(k, '(not set)')}")

# Check if .env is loaded and what it set
env_path = "/opt/airflow/backend/../.env"  # simulating PROJECT_ROOT/.env
print(f"\n=== .env check ===")
print(f"  /opt/airflow/.env exists: {os.path.exists('/opt/airflow/.env')}")
print(f"  /opt/airflow/backend/.env exists: {os.path.exists('/opt/airflow/backend/.env')}")

from pathlib import Path
settings_path = Path("/opt/airflow/backend/config/settings.py").resolve()
project_root = settings_path.parents[2]
print(f"  PROJECT_ROOT = {project_root}")
print(f"  .env at PROJECT_ROOT = {project_root / '.env'}")
print(f"  .env exists? {(project_root / '.env').exists()}")
