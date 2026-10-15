import pandas as pd

print("=== TRAINING DATA ===")
df_train = pd.read_excel("/opt/airflow/Data/data fix/training_dataset_full.xlsx")
print(f"Shape: {df_train.shape}")
print(f"Columns: {list(df_train.columns)}")
print(f"\nRequired features check:")
required = ["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk", "label"]
for col in required:
    if col in df_train.columns:
        print(f"  ✅ {col}: {df_train[col].dtype}")
    else:
        print(f"  ❌ {col}: MISSING")
print(f"\nLabel distribution:")
print(df_train["label"].value_counts().sort_index())

print("\n=== INFERENCE DATA ===")
df_inf = pd.read_excel("/opt/airflow/Data/data fix/inference_dataset_full.xlsx")
print(f"Shape: {df_inf.shape}")
print(f"Columns: {list(df_inf.columns)}")
print(f"\nRequired features check:")
required_inf = ["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk", "id_mahasiswa"]
for col in required_inf:
    if col in df_inf.columns:
        print(f"  ✅ {col}: {df_inf[col].dtype}")
    else:
        print(f"  ❌ {col}: MISSING")
print(f"\nAngkatan unique: {sorted(df_inf['angkatan'].unique())}")