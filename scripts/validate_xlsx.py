"""
Validate local xlsx files: row count, schema, data types.
"""
import pandas as pd
import os

base = "D:\\TA\\TugasAkhirNita\\Data"

files = {
    "training_dataset_fix (1).xlsx": "BEFORE feature engineering",
    "inference_dataset_fix (1).xlsx": "BEFORE feature engineering",
    "data_training_baru(fix).xlsx": "AFTER feature engineering",
    "data_inference_baru(fix).xlsx": "AFTER feature engineering + predictions",
    "hasil_prediksi(fix).xlsx": "Final prediction results",
}

for fname, desc in files.items():
    fpath = os.path.join(base, fname)
    if not os.path.exists(fpath):
        print(f"MISSING: {fname}")
        continue
    
    df = pd.read_excel(fpath)
    print(f"\n=== {fname} ===")
    print(f"  Description: {desc}")
    print(f"  Rows: {df.shape[0]}")
    print(f"  Columns: {df.shape[1]}")
    print(f"  Column names: {list(df.columns)}")
    print(f"  Dtypes:")
    for col in df.columns:
        print(f"    {col:30s} {df[col].dtype}  nulls={df[col].isnull().sum()}")
