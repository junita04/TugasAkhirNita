import pandas as pd
import hashlib
import os

files_to_check = [
    "D:/TA/TugasAkhirNita/Data/data_training_baru(fix).xlsx",
    "D:/TA/TugasAkhirNita/Data/training_dataset_fix.xlsx",
    "D:/TA/TugasAkhirNita/Data/data fix/training_dataset_full.xlsx",
]

for path in files_to_check:
    if os.path.exists(path):
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        print(f"\n{'='*60}")
        print(f"FILE: {os.path.basename(path)}")
        print(f"Path: {path}")
        print(f"Size: {size:,} bytes")
        print(f"MD5: {file_hash}")
        
        df = pd.read_excel(path)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        if "label" in df.columns:
            print(f"Label dist:\n{df['label'].value_counts().sort_index()}")
            print(f"Total: {len(df)} | 0: {(df['label']==0).sum()} | 1: {(df['label']==1).sum()}")
        
        features = ["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk"]
        for col in features:
            if col in df.columns:
                print(f"  {col}: unique={df[col].nunique()}, min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}")
    else:
        print(f"\nNOT FOUND: {path}")