import pandas as pd
import hashlib

print("=== FILE INFO ===")
import os
path = "/opt/airflow/Data/data fix/inference_dataset_full.xlsx"
size = os.path.getsize(path)
print(f"File: {path}")
print(f"Size: {size:,} bytes ({size/1024/1024:.2f} MB)")

with open(path, "rb") as f:
    file_hash = hashlib.md5(f.read()).hexdigest()
print(f"MD5: {file_hash}")

print("\n=== DATA STRUCTURE ===")
df = pd.read_excel(path)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

print("\n=== FEATURE STATS ===")
features = ["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk"]
for col in features:
    print(f"\n{col}:")
    print(f"  dtype: {df[col].dtype}")
    print(f"  unique: {df[col].nunique()}")
    print(f"  min: {df[col].min()}")
    print(f"  max: {df[col].max()}")
    print(f"  mean: {df[col].mean():.2f}")
    if df[col].nunique() <= 20:
        print(f"  value_counts:\n{df[col].value_counts().sort_index()}")

print("\n=== ANGKATAN ===")
print(f"Unique: {sorted(df['angkatan'].unique())}")
print(df["angkatan"].value_counts().sort_index())

print("\n=== SAMPLE ROWS ===")
print(df[features + ["id_mahasiswa"]].head(10).to_string())