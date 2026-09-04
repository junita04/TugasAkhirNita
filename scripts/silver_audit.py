import sys
sys.path.insert(0, '/opt/airflow')
from backend.spark.session import get_spark
from pyspark.sql import functions as F

spark = get_spark('SilverAudit')

bronze = spark.table('iceberg.bronze.data_referensi_mahasiswa')
bronze_count = bronze.count()
bronze_distinct = bronze.select('ID_MHS').distinct().count()

print('=== BRONZE ===')
print(f'Total rows: {bronze_count}')
print(f'Distinct ID: {bronze_distinct}')

from backend.silver.silver import _apply_column_map, _trim_string_columns, SILVER_SPECS

silver_name, column_map = SILVER_SPECS['data_referensi_mahasiswa']
df = _apply_column_map(bronze, column_map)
df = _trim_string_columns(df)
df = df.na.drop(how='all')
after_trim = df.count()

print()
print('=== AFTER COLUMN MAP & TRIM ===')
print(f'Total rows: {after_trim}')

df = df.withColumn('tanggal_masuk', F.col('tanggal_masuk').cast('date'))
df = df.withColumn('tanggal_keluar', F.col('tanggal_keluar').cast('date'))
df = df.withColumn('ipk', F.col('ipk').cast('double'))
df = df.withColumn('total_sks', F.col('total_sks').cast('int'))
df = df.withColumn('jumlah_mk', F.col('jumlah_mk').cast('int'))

null_tanggal_masuk = df.filter(F.col('tanggal_masuk').isNull()).count()
keluar_masuk_rusak = df.filter(
    F.col('tanggal_masuk').isNotNull() &
    F.col('tanggal_keluar').isNotNull() &
    (F.col('tanggal_keluar') < F.col('tanggal_masuk'))
).count()
ipk_oor = df.filter(
    F.col('ipk').isNotNull() & ((F.col('ipk') < 0) | (F.col('ipk') > 4))
).count()

print()
print('=== FILTER AUDIT ===')
print(f'null_tanggal_masuk: {null_tanggal_masuk}')
print(f'keluar_masuk_rusak: {keluar_masuk_rusak}')
print(f'ipk_out_of_range: {ipk_oor}')
total_excluded = null_tanggal_masuk + keluar_masuk_rusak + ipk_oor
print(f'Total excluded: {total_excluded}')
print(f'Expected Silver: {after_trim - total_excluded}')

silver = spark.table('iceberg.silver.silver_mahasiswa')
silver_count = silver.count()
silver_distinct = silver.select('id_mahasiswa').distinct().count()
print()
print('=== CURRENT SILVER ===')
print(f'Total rows: {silver_count}')
print(f'Distinct ID: {silver_distinct}')

kept_basic = df.filter(F.col('tanggal_masuk').isNotNull()).filter(
    ~(F.col('tanggal_keluar').isNotNull() & (F.col('tanggal_keluar') < F.col('tanggal_masuk')))
)
kept_basic_count = kept_basic.count()
print()
print(f'After tanggal filters: {kept_basic_count}')

# IPK distribution
ipk_null = kept_basic.filter(F.col('ipk').isNull()).count()
ipk_neg = kept_basic.filter(F.col('ipk').isNotNull() & (F.col('ipk') < 0)).count()
ipk_over = kept_basic.filter(F.col('ipk').isNotNull() & (F.col('ipk') > 4)).count()
ipk_valid = kept_basic.filter(F.col('ipk').isNull() | ((F.col('ipk') >= 0) & (F.col('ipk') <= 4))).count()

print()
print('=== IPK AUDIT (after tanggal filters) ===')
print(f'IPK NULL: {ipk_null}')
print(f'IPK < 0: {ipk_neg}')
print(f'IPK > 4: {ipk_over}')
print(f'IPK valid (0-4 or NULL): {ipk_valid}')
print(f'Total after IPK filter: {ipk_valid}')

# Check what IPK values are > 4
if ipk_over > 0:
    print()
    print('=== IPK > 4 SAMPLES ===')
    over_samples = kept_basic.filter(F.col('ipk') > 4).select('id_mahasiswa', 'ipk', 'total_sks', 'status_mahasiswa').limit(10)
    over_samples.show()

spark.stop()
