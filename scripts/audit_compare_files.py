"""Audit: Compare all source Excel files."""
import pandas as pd
import os

files = {
    'original': r'D:\TA\TugasAkhirNita\Data\(asli)req_data_rut.xlsx',
    '(1)': r'D:\TA\TugasAkhirNita\Data\(asli)req_data_rut (1).xlsx',
    'baru': r'D:\TA\TugasAkhirNita\Data\(asli)req_data_rut (baru).xlsx',
    'baruu': r'D:\TA\TugasAkhirNita\Data\(asli)req_data_rut (baruu).xlsx',
    'baruuu': r'D:\TA\TugasAkhirNita\Data\(asli)req_data_rut (baruuu).xlsx',
}

print("=" * 70)
print("SOURCE FILE COMPARISON")
print("=" * 70)

for label, f in files.items():
    name = os.path.basename(f)
    size = os.path.getsize(f)
    df = pd.read_excel(f, sheet_name='Referensi Data Mahasiswa')
    khs = pd.read_excel(f, sheet_name='Data KHS')

    print(f"\n--- {label}: {name} ---")
    print(f"  Size: {size/1024:.1f} KB")
    print(f"  Referensi: {len(df)} rows x {len(df.columns)} cols")
    print(f"  KHS: {len(khs)} rows x {len(khs.columns)} cols")
    print(f"  First col name: '{df.columns[0]}'")
    print(f"  First 5 IDs: {df.iloc[:5, 0].tolist()}")
    print(f"  Last 5 IDs: {df.iloc[-5:, 0].tolist()}")
    print(f"  Total SKS sum: {df['Total SKS'].sum()}")
    print(f"  IPK mean: {df['IPK'].mean():.4f}")
    print(f"  Status dist: {df['Status Mahasiswa'].value_counts().to_dict()}")
    print(f"  KHS columns: {list(khs.columns)}")

# Check if baru and baruu are identical
print("\n" + "=" * 70)
print("IDENTITY CHECK: baru vs baruu vs baruuu")
print("=" * 70)

baru = pd.read_excel(files['baru'], sheet_name='Referensi Data Mahasiswa')
baruu = pd.read_excel(files['baruu'], sheet_name='Referensi Data Mahasiswa')
baruuu = pd.read_excel(files['baruuu'], sheet_name='Referensi Data Smart')

# Compare column names
print(f"baru columns: {list(baru.columns)}")
print(f"baruu columns: {list(baruu.columns)}")

# Compare first IDs
print(f"\nbaru first 5: {baru.iloc[:5, 0].tolist()}")
print(f"baruu first 5: {baruu.iloc[:5, 0].tolist()}")

# Compare Total SKS
print(f"\nbaru Total SKS sum: {baru['Total SKS'].sum()}")
print(f"baruu Total SKS sum: {baruu['Total SKS'].sum()}")
print(f"baruuu Total SKS sum: N/A (read error)")

# Check if data is identical
if baru.shape == baruu.shape:
    identical = (baru.values == baruu.values).all()
    print(f"\nbaru vs baruu: {'IDENTICAL' if identical else 'DIFFERENT'}")
else:
    print(f"\nbaru vs baruu: DIFFERENT SHAPES {baru.shape} vs {baruu.shape}")
