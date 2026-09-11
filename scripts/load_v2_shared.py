"""
Phase 1 (revised): Read Excel files and save as Parquet to SHARED location.
/opt/airflow/data is mounted from host and accessible by both scheduler and worker.
"""
import os
import pandas as pd

DATA_DIR = "/opt/airflow/data"
PARQUET_DIR = "/opt/airflow/data/parquet_v2"

os.makedirs(PARQUET_DIR, exist_ok=True)

print("=" * 70)
print("PHASE 1: READING EXCEL FILES -> PARQUET (shared location)")
print("=" * 70)

# File 1: training_dataset_fix (1).xlsx
f1 = os.path.join(DATA_DIR, "training_dataset_fix (1).xlsx")
print(f"\nReading: {f1}")
df_train = pd.read_excel(f1)
print(f"  Rows: {len(df_train)}, Columns: {len(df_train.columns)}")
print(f"  Columns: {list(df_train.columns)}")
train_parquet = os.path.join(PARQUET_DIR, "training_dataset_v2")
df_train.to_parquet(train_parquet, index=False, engine="pyarrow")
print(f"  Saved: {train_parquet}")

# File 2: inference_dataset_fix (1).xlsx
f2 = os.path.join(DATA_DIR, "inference_dataset_fix (1).xlsx")
print(f"\nReading: {f2}")
df_infer = pd.read_excel(f2)
print(f"  Rows: {len(df_infer)}, Columns: {len(df_infer.columns)}")
print(f"  Columns: {list(df_infer.columns)}")
infer_parquet = os.path.join(PARQUET_DIR, "inference_dataset_v2")
df_infer.to_parquet(infer_parquet, index=False, engine="pyarrow")
print(f"  Saved: {infer_parquet}")

# File 3: hasil_prediksi(fix).xlsx
f3 = os.path.join(DATA_DIR, "hasil_prediksi(fix).xlsx")
print(f"\nReading: {f3}")
df_pred = pd.read_excel(f3)
print(f"  Rows: {len(df_pred)}, Columns: {len(df_pred.columns)}")
print(f"  Columns: {list(df_pred.columns)}")
pred_parquet = os.path.join(PARQUET_DIR, "model_predictions_v2")
df_pred.to_parquet(pred_parquet, index=False, engine="pyarrow")
print(f"  Saved: {pred_parquet}")

print("\n" + "=" * 70)
print("PHASE 1 COMPLETE")
print("=" * 70)

# List files
import subprocess
result = subprocess.run(["ls", "-la", PARQUET_DIR], capture_output=True, text=True)
print(result.stdout)
