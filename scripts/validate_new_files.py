"""
Validate the 5 new data files from Google Colab.
Read-only, no modifications.
"""
import pandas as pd
import os

data_dir = r"D:\TA\TugasAkhirNita\Data"

files = {
    "training_dataset_fix (1).xlsx": "Training Dataset (before feature engineering)",
    "inference_dataset_fix (1).xlsx": "Inference Dataset (before feature engineering)",
    "data_training_baru(fix).xlsx": "Training Dataset (after feature engineering)",
    "data_inference_baru(fix).xlsx": "Inference Dataset (after feature engineering)",
    "hasil_prediksi(fix).xlsx": "Prediction Results",
}

expected_features = [
    "angkatan_enc", "IP_kategori", "IPK_kategori",
    "total_sks", "selisih_sks", "ip_x_progress", "rasio_sks_mk"
]

for fname, desc in files.items():
    fpath = os.path.join(data_dir, fname)
    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    print(f"DESCRIPTION: {desc}")
    print(f"{'='*70}")
    
    if not os.path.exists(fpath):
        print(f"  FILE NOT FOUND: {fpath}")
        continue
    
    try:
        xl = pd.ExcelFile(fpath)
        print(f"  Sheets: {xl.sheet_names}")
        
        for sheet in xl.sheet_names:
            df = pd.read_excel(fpath, sheet_name=sheet)
            print(f"\n  --- Sheet: {sheet} ---")
            print(f"  Rows: {len(df)}")
            print(f"  Columns: {len(df.columns)}")
            print(f"  Column names: {list(df.columns)}")
            print(f"  Data types:")
            for col in df.columns:
                print(f"    {col}: {df[col].dtype}")
            
            # Missing values
            missing = df.isnull().sum()
            if missing.sum() > 0:
                print(f"  Missing values:")
                for col, cnt in missing.items():
                    if cnt > 0:
                        print(f"    {col}: {cnt}")
            else:
                print(f"  Missing values: NONE")
            
            # Duplicates
            dup = df.duplicated().sum()
            print(f"  Duplicates: {dup}")
            
            # First 5 rows
            print(f"\n  First 5 rows:")
            print(df.head().to_string(index=False))
            
            # Check for expected features
            if desc == "Training Dataset (after feature engineering)" or desc == "Inference Dataset (after feature engineering)":
                missing_features = [f for f in expected_features if f not in df.columns]
                extra_features = [f for c in df.columns if c not in expected_features and c not in ["id_mahasiswa", "id_mhs", "label", "jk_enc", "angkatan", "ip", "ipk", "jumlah_mk", "sks_seharusnya", "persentase_sks", "lama_studi"]]
                if missing_features:
                    print(f"\n  MISSING EXPECTED FEATURES: {missing_features}")
                else:
                    print(f"\n  ALL 7 EXPECTED FEATURES PRESENT")
            
            # Label distribution for training
            if "label" in df.columns and desc == "Training Dataset (after feature engineering)":
                print(f"\n  Label distribution:")
                print(f"    {df['label'].value_counts().to_dict()}")
            
            # Prediction distribution for hasil_prediksi
            if "Prediksi" in df.columns and desc == "Prediction Results":
                print(f"\n  Prediction distribution:")
                print(f"    {df['Prediksi'].value_counts().to_dict()}")
            elif "prediksi" in df.columns and desc == "Prediction Results":
                print(f"\n  Prediction distribution:")
                print(f"    {df['prediksi'].value_counts().to_dict()}")
    except Exception as e:
        print(f"  ERROR: {e}")
