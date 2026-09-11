"""
Phase 1-5: Load new data from Google Colab into Iceberg tables.
- feature_store.training_dataset_v2
- feature_store.inference_dataset_v2
- gold.model_predictions_v2
- gold.prediction_by_angkatan_v2

Strategy: Pandas reads Excel -> Parquet -> Spark reads Parquet -> Iceberg
"""
import sys
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# =====================================================
# PHASE 1: Read Excel files and save as Parquet
# =====================================================

DATA_DIR = "/opt/airflow/data"
PARQUET_DIR = "/tmp/parquet_v2"

os.makedirs(PARQUET_DIR, exist_ok=True)

print("=" * 70)
print("PHASE 1: READING EXCEL FILES")
print("=" * 70)

# File 1: training_dataset_fix (1).xlsx -> training parquet
f1 = os.path.join(DATA_DIR, "training_dataset_fix (1).xlsx")
print(f"\nReading: {f1}")
df_train = pd.read_excel(f1)
print(f"  Rows: {len(df_train)}, Columns: {len(df_train.columns)}")
print(f"  Columns: {list(df_train.columns)}")
train_parquet = os.path.join(PARQUET_DIR, "training_dataset_v2.parquet")
df_train.to_parquet(train_parquet, index=False)
print(f"  Saved: {train_parquet}")

# File 2: inference_dataset_fix (1).xlsx -> inference parquet
f2 = os.path.join(DATA_DIR, "inference_dataset_fix (1).xlsx")
print(f"\nReading: {f2}")
df_infer = pd.read_excel(f2)
print(f"  Rows: {len(df_infer)}, Columns: {len(df_infer.columns)}")
print(f"  Columns: {list(df_infer.columns)}")
infer_parquet = os.path.join(PARQUET_DIR, "inference_dataset_v2.parquet")
df_infer.to_parquet(infer_parquet, index=False)
print(f"  Saved: {infer_parquet}")

# File 3: hasil_prediksi(fix).xlsx -> predictions parquet
f3 = os.path.join(DATA_DIR, "hasil_prediksi(fix).xlsx")
print(f"\nReading: {f3}")
df_pred = pd.read_excel(f3)
print(f"  Rows: {len(df_pred)}, Columns: {len(df_pred.columns)}")
print(f"  Columns: {list(df_pred.columns)}")
pred_parquet = os.path.join(PARQUET_DIR, "model_predictions_v2.parquet")
df_pred.to_parquet(pred_parquet, index=False)
print(f"  Saved: {pred_parquet}")

print("\n" + "=" * 70)
print("PHASE 1 COMPLETE: Excel -> Parquet")
print("=" * 70)

# =====================================================
# Validate parquet files
# =====================================================
print("\nValidating parquet files...")

pq_train = pq.read_table(train_parquet)
print(f"  Training: {pq_train.num_rows} rows, {len(pq_train.column_names)} cols")

pq_infer = pq.read_table(infer_parquet)
print(f"  Inference: {pq_infer.num_rows} rows, {len(pq_infer.column_names)} cols")

pq_pred = pq.read_table(pred_parquet)
print(f"  Predictions: {pq_pred.num_rows} rows, {len(pq_pred.column_names)} cols")

print("\nAll parquet files validated successfully.")
