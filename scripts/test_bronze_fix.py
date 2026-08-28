import sys
sys.path.insert(0, "/opt/airflow")

from pathlib import Path
from backend.bronze.bronze import load_all_sheets_to_bronze

file_path = Path("/opt/airflow/data/(asli)req_data_rut (1).xlsx")

success, skipped = load_all_sheets_to_bronze(file_path)

print(f"\nResult: success={success}, skipped={skipped}")
