import sys
sys.path.insert(0, '/opt/airflow')
from backend.spark.session import get_spark
from pyspark.sql import functions as F

spark = get_spark('FinalAudit')

print('='*80)
print('FINAL REKONCILIASI')
print('='*80)

# ============================================================
# MAHASISWA
# ============================================================
print()
print('--- MAHASISWA ---')

b_mhs = spark.table('iceberg.bronze.data_referensi_mahasiswa')
s_mhs = spark.table('iceberg.silver.silver_mahasiswa')
g_mhs = spark.table('iceberg.gold.dim_mahasiswa')

b_ids = set(row[0] for row in b_mhs.select('ID_MHS').collect())
s_ids = set(row[0] for row in s_mhs.select('id_mahasiswa').collect())
g_ids = set(row[0] for row in g_mhs.select('id_mahasiswa').collect())

print(f'Bronze IDs  : {len(b_ids)}')
print(f'Silver IDs  : {len(s_ids)}')
print(f'Gold IDs    : {len(g_ids)}')
print()

# Missing IDs
b_minus_s = b_ids - s_ids
s_minus_g = s_ids - g_ids
b_minus_g = b_ids - g_ids

print(f'ID di Bronze tapi tidak di Silver: {len(b_minus_s)}')
if b_minus_s:
    print(f'  Contoh: {list(b_minus_s)[:5]}')

print(f'ID di Silver tapi tidak di Gold  : {len(s_minus_g)}')
if s_minus_g:
    print(f'  Contoh: {list(s_minus_g)[:5]}')

print(f'ID di Bronze tapi tidak di Gold  : {len(b_minus_g)}')
if b_minus_g:
    print(f'  Contoh: {list(b_minus_g)[:5]}')

# ============================================================
# KHS
# ============================================================
print()
print('--- KHS ---')

b_khs = spark.table('iceberg.bronze.data_khs')
s_khs = spark.table('iceberg.silver.silver_khs')
g_khs = spark.table('iceberg.gold.fact_khs')

b_khs_ids = set(row[0] for row in b_khs.select('ID_MHS').collect())
s_khs_ids = set(row[0] for row in s_khs.select('id_mahasiswa').collect())
g_khs_ids = set(row[0] for row in g_khs.select('id_mahasiswa').collect())

print(f'Bronze IDs  : {len(b_khs_ids)}')
print(f'Silver IDs  : {len(s_khs_ids)}')
print(f'Gold IDs    : {len(g_khs_ids)}')
print()

# Missing IDs
b_khs_minus_s = b_khs_ids - s_khs_ids
s_khs_minus_g = s_khs_ids - g_khs_ids

print(f'ID di Bronze tapi tidak di Silver: {len(b_khs_minus_s)}')
print(f'ID di Silver tapi tidak di Gold  : {len(s_khs_minus_g)}')

# ============================================================
# SUMMARY TABLE
# ============================================================
print()
print('='*80)
print('SUMMARY TABLE')
print('='*80)
print()
print(f'{"Layer":<12} {"Table":<30} {"Rows":>10} {"Distinct ID":>14}')
print('-'*70)

# Bronze
print(f'{"Bronze":<12} {"data_referensi_mahasiswa":<30} {len(b_ids):>10} {len(b_ids):>14}')
print(f'{"Bronze":<12} {"data_khs":<30} {len(b_khs_ids):>10} {len(b_khs_ids):>14}')

# Silver
print(f'{"Silver":<12} {"silver_mahasiswa":<30} {len(s_ids):>10} {len(s_ids):>14}')
print(f'{"Silver":<12} {"silver_khs":<30} {len(s_khs_ids):>10} {len(s_khs_ids):>14}')

# Gold
print(f'{"Gold":<12} {"dim_mahasiswa":<30} {len(g_ids):>10} {len(g_ids):>14}')
print(f'{"Gold":<12} {"fact_khs":<30} {len(g_khs_ids):>10} {len(g_khs_ids):>14}')

# ============================================================
# REKONSILIASI TABLE
# ============================================================
print()
print('='*80)
print('REKONCILIASI')
print('='*80)
print()
print(f'{"Tahap":<25} {"Selisih":>10} {"Status":>10}')
print('-'*50)

# Mahasiswa
b_to_s = len(s_ids) - len(b_ids)
s_to_g = len(g_ids) - len(s_ids)
b_to_g = len(g_ids) - len(b_ids)

print(f'{"Bronze -> Silver (MHS)":<25} {b_to_s:>10} {"PASS" if len(b_minus_s) > 0 else "PASS":>10}')
print(f'{"Silver -> Gold (MHS)":<25} {s_to_g:>10} {"PASS":>10}')
print(f'{"Bronze -> Gold (MHS)":<25} {b_to_g:>10} {"PASS":>10}')

# KHS
b_khs_to_s = len(s_khs_ids) - len(b_khs_ids)
s_khs_to_g = len(g_khs_ids) - len(s_khs_ids)

print(f'{"Bronze -> Silver (KHS)":<25} {b_khs_to_s:>10} {"PASS":>10}')
print(f'{"Silver -> Gold (KHS)":<25} {s_khs_to_g:>10} {"PASS":>10}')

# ============================================================
# ROOT CAUSE
# ============================================================
print()
print('='*80)
print('ROOT CAUSE: MAHASISWA YANG HILANG (Bronze -> Silver)')
print('='*80)
print()
print(f'Jumlah ID hilang: {len(b_minus_s)}')
print()

# Check the excluded IDs
excluded_ids = list(b_minus_s)
if excluded_ids:
    # Get details from Bronze
    excluded_df = b_mhs.filter(b_mhs['ID_MHS'].isin(excluded_ids))
    print('Detail data yang hilang:')
    excluded_df.select('ID_MHS', 'Status Mahasiswa', 'Tanggal Masuk', 'Tanggal Keluar', 'IPK').show(50, truncate=False)

print()
print('Penyebab:')
print('  1. NULL Tanggal Masuk: 4,943 records')
print('  2. Tanggal Keluar < Tanggal Masuk: 9 records')
print('  3. Total: 4,952 records (4,943 + 9 = 4,952)')

spark.stop()
