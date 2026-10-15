import pandas as pd
import hashlib

print("=== FILE INFO ===")
import os
path = "/opt/airflow/Data/data fix/training_dataset_full.xlsx"
size = os.path.getsize(path)
print(f"File: {path}")
print(f"Size: {size:,} bytes ({size/1024/1024:.2f} MB)")

# Hash
with open(path, "rb") as f:
    file_hash = hashlib.md5(f.read()).hexdigest()
print(f"MD5: {file_hash}")

print("\n=== DATA STRUCTURE ===")
df = pd.read_excel(path)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Dtypes:\n{df.dtypes}")

print("\n=== LABEL DISTRIBUTION ===")
print(df["label"].value_counts().sort_index())
print(f"Total: {len(df)}")
print(f"0 (Tepat): {(df['label']==0).sum()} ({(df['label']==0).mean()*100:.1f}%)")
print(f"1 (Terlambat): {(df['label']==1).sum()} ({(df['label']==1).mean()*100:.1f}%)")

print("\n=== FEATURE STATS ===")
features = ["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk"]
for col in features:
    print(f"\n{col}:")
    print(f"  dtype: {df[col].dtype}")
    print(f"  unique: {df[col].nunique()}")
    print(f"  min: {df[col].min()}")
    print(f"  max: {df[col].max()}")
    print(f"  mean: {df[col].mean():.2f}")
    print(f"  null: {df[col].isnull().sum()}")
    if df[col].nunique() <= 20:
        print(f"  value_counts:\n{df[col].value_counts().sort_index()}")

print("\n=== OTHER COLUMNS (non-features) ===")
other_cols = [c for c in df.columns if c not in features + ["label", "id"]]
for col in other_cols:
    print(f"\n{col}:")
    print(f"  dtype: {df[col].dtype}")
    print(f"  unique: {df[col].nunique()}")
    if df[col].nunique() <= 20:
        print(f"  value_counts:\n{df[col].value_counts().sort_index()}")

print("\n=== SAMPLE ROWS ===")
print(df[features + ["label"]].head(10).to_string())