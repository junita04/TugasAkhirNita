"""
Compare local xlsx files with Iceberg data.
"""
import pandas as pd

base = "D:\\TA\\TugasAkhirNita\\Data"

files = {
    "training_dataset_fix (1).xlsx": "BEFORE feature engineering",
    "inference_dataset_fix (1).xlsx": "BEFORE feature engineering",
    "data_training_baru(fix).xlsx": "AFTER feature engineering",
    "data_inference_baru(fix).xlsx": "AFTER feature engineering + predictions",
    "hasil_prediksi(fix).xlsx": "Final prediction results",
}

for fname, desc in files.items():
    import os
    fpath = os.path.join(base, fname)
    df = pd.read_excel(fpath)
    print(f"\n=== {fname} ===")
    print(f"  Description: {desc}")
    print(f"  Rows: {df.shape[0]}")
    print(f"  Columns: {df.shape[1]}")
    print(f"  Column names: {list(df.columns)}")
    print(f"  Unique id_mahasiswa: {df['id_mahasiswa'].nunique()}")
    print(f"  Duplicates: {df.shape[0] - df['id_mahasiswa'].nunique()}")
    
    # Check prediction distribution if available
    if 'Prediksi' in df.columns:
        print(f"  Prediksi distribution:")
        for val, cnt in df['Prediksi'].value_counts().items():
            print(f"    {val}: {cnt}")
    if 'Prediksi_Label' in df.columns:
        print(f"  Prediksi_Label distribution:")
        for val, cnt in df['Prediksi_Label'].value_counts().items():
            print(f"    {val}: {cnt}")

# Compare schemas
print("\n\n=== SCHEMA COMPARISON ===")
df_train = pd.read_excel(os.path.join(base, "training_dataset_fix (1).xlsx"))
df_train_new = pd.read_excel(os.path.join(base, "data_training_baru(fix).xlsx"))
df_inf = pd.read_excel(os.path.join(base, "inference_dataset_fix (1).xlsx"))
df_inf_new = pd.read_excel(os.path.join(base, "data_inference_baru(fix).xlsx"))
df_pred = pd.read_excel(os.path.join(base, "hasil_prediksi(fix).xlsx"))

print("\ntraining_dataset_fix (1).xlsx columns:")
for c in df_train.columns:
    print(f"  {c}")

print("\ndata_training_baru(fix).xlsx columns:")
for c in df_train_new.columns:
    print(f"  {c}")

print("\ninference_dataset_fix (1).xlsx columns:")
for c in df_inf.columns:
    print(f"  {c}")

print("\ndata_inference_baru(fix).xlsx columns:")
for c in df_inf_new.columns:
    print(f"  {c}")

print("\nhasil_prediksi(fix).xlsx columns:")
for c in df_pred.columns:
    print(f"  {c}")
