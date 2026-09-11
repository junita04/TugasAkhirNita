"""
Fix MinIO upload - properly quote filenames with special characters.
"""
import subprocess
import os

DATA_DIR = "/opt/airflow/data"
minio_source = "local/warehouse/source"

# Ensure target exists
subprocess.run(["mc", "mb", "local/warehouse/source"], capture_output=True)

xlsx_files = [
    "training_dataset_fix (1).xlsx",
    "inference_dataset_fix (1).xlsx",
    "data_training_baru(fix).xlsx",
    "data_inference_baru(fix).xlsx",
    "hasil_prediksi(fix).xlsx",
]

for fname in xlsx_files:
    src = os.path.join(DATA_DIR, fname)
    if not os.path.exists(src):
        print(f"  SKIP: {fname}")
        continue
    
    # Use list form to avoid shell quoting issues
    dst = f"{minio_source}/{fname}"
    result = subprocess.run(["mc", "cp", src, dst], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Uploaded: {fname}")
    else:
        print(f"  ERROR: {fname}: {result.stderr}")

# Verify
print("\nVerifying MinIO contents:")
result = subprocess.run(["mc", "ls", minio_source], capture_output=True, text=True)
print(result.stdout)
