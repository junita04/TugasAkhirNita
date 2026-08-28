import sys, subprocess, json, os
sys.path.insert(0, "/opt/airflow")

from pathlib import Path

file_path = Path("/opt/airflow/data/(asli)req_data_rut (1).xlsx")
sheet = "Referensi Data Mahasiswa"
table_name = "data_referensi_mahasiswa"

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

print(f"returncode={proc.returncode}")
print(f"stdout len={len(proc.stdout)}")
print(f"stderr len={len(proc.stderr)}")
print(f"stdout last 1000: {proc.stdout[-1000:]}")
print(f"stderr last 500: {proc.stderr[-500:]}")
