"""STEP 1: Audit Source Excel"""
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]
EXCEL_FILE = "/tmp/(asli)req_data_rut (baru).xlsx"
SHEET = "Referensi Data Mahasiswa"

print("=" * 70)
print("STEP 1: AUDIT SOURCE EXCEL")
print("=" * 70)

xl = pd.ExcelFile(EXCEL_FILE)
print(f"Sheets: {xl.sheet_names}")

df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET, dtype=str)
print(f"\nSheet: {SHEET}")
print(f"  Rows: {len(df)}")
print(f"  Columns: {len(df.columns)}")
print(f"  Column names: {list(df.columns)}")

# Normalize column names
df.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df.columns]

# Unique ID
unique_ids = df["id_mhs"].nunique()
dup_count = len(df) - unique_ids
print(f"  Unique IDs: {unique_ids}")
print(f"  Duplicate IDs: {dup_count}")

# Status distribution
print(f"\nStatus Mahasiswa distribution:")
status_dist = df["status_mahasiswa"].value_counts()
for s, c in status_dist.items():
    print(f"  {s}: {c}")

# NULL tanggal_keluar
null_tgl_keluar = df["tanggal_keluar"].isna().sum()
print(f"\nNULL tanggal_keluar: {null_tgl_keluar}")

# Angkatan 2023
df["angkatan"] = df["tanggal_masuk"].apply(lambda x: str(x)[:4] if pd.notna(x) else None)
angkatan_2023 = df[df["angkatan"] == "2023"]
print(f"\nAngkatan 2023 total: {len(angkatan_2023)}")
aktif_2023 = angkatan_2023[angkatan_2023["status_mahasiswa"] == "AKTIF"]
lulus_2023 = angkatan_2023[angkatan_2023["status_mahasiswa"] == "Lulus"]
print(f"Angkatan 2023 AKTIF: {len(aktif_2023)}")
print(f"Angkatan 2023 LULUS: {len(lulus_2023)}")

# Check 3 target IDs
print(f"\n{'='*70}")
print("3 TARGET IDs — SOURCE DATA")
print(f"{'='*70}")
for mid in TARGET_IDS:
    row = df[df["id_mhs"] == mid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"\n{mid}:")
        print(f"  Jenis Kelamin: {r.get('jenis_kelamin', 'N/A')}")
        print(f"  Tanggal Masuk: {r.get('tanggal_masuk', 'N/A')}")
        print(f"  Tanggal Keluar: {r.get('tanggal_keluar', 'N/A')}")
        print(f"  IPK: {r.get('ipk', 'N/A')}")
        print(f"  Total SKS: {r.get('total_sks', 'N/A')}")
        print(f"  Jumlah MK: {r.get('jumlah_mk', 'N/A')}")
        print(f"  Status: {r.get('status_mahasiswa', 'N/A')}")
    else:
        print(f"\n{mid}: NOT FOUND IN SOURCE!")

print("\nSTEP 1 COMPLETE")
