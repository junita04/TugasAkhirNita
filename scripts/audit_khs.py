"""Audit KHS sheet — Check if KHS has data that could change status"""
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

print("=" * 70)
print("AUDIT KHS SHEET — CHECK FOR STATUS-CHANGING DATA")
print("=" * 70)

# Read both Excel files
for label, path in [("OLD Excel", "/tmp/(asli)req_data_rut (baru).xlsx"), ("NEW Excel", "/tmp/new_data.xlsx")]:
    print(f"\n{'='*70}")
    print(f"{label}: {path}")
    print(f"{'='*70}")
    
    try:
        # Read all sheets
        xl = pd.ExcelFile(path)
        print(f"Sheets: {xl.sheet_names}")
        
        # Check Data KHS sheet
        if "Data KHS" in xl.sheet_names:
            df_khs = pd.read_excel(path, sheet_name="Data KHS", dtype=str)
            print(f"\nData KHS: {len(df_khs)} rows, {len(df_khs.columns)} columns")
            print(f"Columns: {list(df_khs.columns)}")
            
            # Normalize columns
            df_khs.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_khs.columns]
            
            # Check for target IDs in KHS
            print(f"\nTarget IDs in KHS:")
            for mid in TARGET_IDS:
                rows = df_khs[df_khs["id_mhs"] == mid] if "id_mhs" in df_khs.columns else pd.DataFrame()
                if len(rows) > 0:
                    print(f"  {mid}: {len(rows)} records found!")
                    print(f"    Columns: {list(rows.columns)}")
                    for _, r in rows.iterrows():
                        print(f"    {dict(r)}")
                else:
                    print(f"  {mid}: NOT in KHS")
        else:
            print("  Data KHS sheet NOT FOUND")
        
        # Check Referensi Data Mahasiswa for target IDs
        print(f"\nReferensi Data Mahasiswa — Target IDs:")
        df_ref = pd.read_excel(path, sheet_name="Referensi Data Mahasiswa", dtype=str)
        df_ref.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_ref.columns]
        for mid in TARGET_IDS:
            row = df_ref[df_ref["id_mhs"] == mid]
            if len(row) > 0:
                r = row.iloc[0]
                print(f"  {mid}: status={r.get('status_mahasiswa', 'N/A')}, tgl_keluar={r.get('tanggal_keluar', 'N/A')}")
        
        # Check ALL sheets for any reference to target IDs
        print(f"\nChecking ALL sheets for target IDs:")
        for sheet in xl.sheet_names:
            try:
                df_sheet = pd.read_excel(path, sheet_name=sheet, dtype=str)
                df_sheet.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_sheet.columns]
                if "id_mhs" in df_sheet.columns:
                    for mid in TARGET_IDS:
                        rows = df_sheet[df_sheet["id_mhs"] == mid]
                        if len(rows) > 0:
                            print(f"  {sheet}: {mid} found ({len(rows)} rows)")
            except:
                pass
                
    except Exception as e:
        print(f"Error: {e}")

# Check the old Excel for any hidden sheets or different data
print(f"\n{'='*70}")
print("DETAILED KHS ANALYSIS — LOOKING FOR STATUS-CHANGING JOINS")
print(f"{'='*70}")

# Read KHS from old file
try:
    df_khs = pd.read_excel("/tmp/(asli)req_data_rut (baru).xlsx", sheet_name="Data KHS", dtype=str)
    df_khs.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_khs.columns]
    
    print(f"KHS columns: {list(df_khs.columns)}")
    print(f"KHS rows: {len(df_khs)}")
    
    # Check if KHS has status_mahasiswa or tanggal_keluar
    status_cols = [c for c in df_khs.columns if "status" in c.lower() or "tanggal" in c.lower() or "keluar" in c.lower()]
    print(f"\nStatus/tanggal columns in KHS: {status_cols}")
    
    # Check unique values in status columns
    for col in status_cols:
        print(f"\n  Unique values in {col}:")
        print(f"    {df_khs[col].value_counts().head(10)}")
        
except Exception as e:
    print(f"Error: {e}")

print("\nKHS AUDIT COMPLETE")
