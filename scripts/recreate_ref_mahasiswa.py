"""
Re-create data_referensi_mahasiswa in Bronze.
Runs the subprocess approach for just this one sheet.
"""
import sys, subprocess, json, os
sys.path.insert(0, "/opt/airflow")

from pathlib import Path
from backend.bronze.bronze import EXPECTED_SHEETS_TO_TABLE, excel_sheet_to_table

file_path = Path("/opt/airflow/data/(asli)req_data_rut (1).xlsx")
sheet = "Referensi Data Mahasiswa"
table_name = EXPECTED_SHEETS_TO_TABLE.get(sheet.strip(), excel_sheet_to_table(sheet))

print(f"Re-creating bronze.{table_name} from sheet '{sheet}'...")

sub_env = os.environ.copy()
sub_env["PYTHONPATH"] = "/opt/airflow"

proc = subprocess.run(
    [
        sys.executable, "-m", "backend.bronze.bronze",
        str(file_path), sheet, table_name,
    ],
    capture_output=True,
    text=True,
    timeout=600,
    env=sub_env,
)

stdout = proc.stdout.strip()
stderr = proc.stderr.strip()

if proc.returncode == 0 and stdout:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            result = json.loads(line)
            print(f"Result: {json.dumps(result, indent=2)}")
            break
    else:
        print(f"No JSON in stdout. stdout tail: {stdout[-500:]}")
else:
    print(f"FAILED: returncode={proc.returncode}")
    if stderr:
        print(f"stderr tail: {stderr[-500:]}")
