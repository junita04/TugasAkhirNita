"""Inspect the actual Excel file for NULL tanggal_masuk"""
import pandas as pd
import numpy as np

path = "/tmp/(asli)req_data_rut (baru).xlsx"
xls = pd.ExcelFile(path)
print(f"Sheet names: {xls.sheet_names}")

for sheet in xls.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet, dtype=str)
    print(f"\n{'='*60}")
    print(f"Sheet: {sheet}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Column count: {len(df.columns)}")

    # Find tanggal_masuk column
    for col in df.columns:
        if 'tanggal' in str(col).lower() and 'masuk' in str(col).lower():
            print(f"\n--- Column: '{col}' ---")
            # Re-read without dtype=str to get actual NaN
            df_raw = pd.read_excel(path, sheet_name=sheet)
            raw_col = df_raw[col]
            print(f"  dtype (raw): {raw_col.dtype}")
            print(f"  NULL (NaN) count: {raw_col.isna().sum()}")
            print(f"  Non-null count: {raw_col.notna().sum()}")
            
            # Now check with dtype=str
            str_col = df[col]
            print(f"  --- With dtype=str ---")
            print(f"  NaN string count: {str_col.isna().sum()}")
            print(f"  'nan' string count: {(str_col == 'nan').sum()}")
            print(f"  'NaN' string count: {(str_col == 'NaN').sum()}")
            print(f"  'None' string count: {(str_col == 'None').sum()}")
            print(f"  'null' string count: {(str_col == 'null').sum()}")
            print(f"  'NULL' string count: {(str_col == 'NULL').sum()}")
            print(f"  '' empty string count: {(str_col == '').sum()}")
            print(f"  '-' dash count: {(str_col == '-').sum()}")
            print(f"  Whitespace-only count: {str_col.apply(lambda x: str(x).strip() == '' if pd.notna(x) else False).sum()}")
            print(f"  Total rows: {len(str_col)}")
            
            # Show unique non-null values
            unique_vals = str_col.dropna().unique()
            print(f"  Unique non-null values (first 20): {unique_vals[:20]}")
            print(f"  Total unique non-null: {len(unique_vals)}")
            
            # Show sample of rows where raw is NaN
            nan_rows = df_raw[df_raw[col].isna()]
            print(f"\n  Sample rows with NULL tanggal_masuk (raw):")
            print(nan_rows.head(10).to_string())
            break
