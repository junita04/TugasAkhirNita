from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from pyspark.sql.functions import col

spark = get_spark("Check Gold")

# ==========================================
# Membaca Gold Mahasiswa
# ==========================================

df = spark.table(f"{ICEBERG_NAMESPACE}.gold.gold_mahasiswa")

print("=" * 60)
print("RINGKASAN GOLD MAHASISWA")
print("=" * 60)

print(f"TOTAL DATA : {df.count()}")

# ==========================================
# Nilai unik status_mahasiswa
# ==========================================

print("\nNilai unik pada kolom status_mahasiswa")
df.select("status_mahasiswa").distinct().show(truncate=False)

# ==========================================
# Jumlah setiap status
# ==========================================

print("\nJumlah setiap status_mahasiswa")
df.groupBy("status_mahasiswa") \
    .count() \
    .orderBy(col("count").desc()) \
    .show(truncate=False)

# ==========================================
# Cek filter 'LULUS'
# ==========================================

jumlah_lulus = df.filter(
    col("status_mahasiswa") == "LULUS"
).count()

print(f"\nJumlah status = 'LULUS' : {jumlah_lulus}")

# ==========================================
# Cek filter 'Lulus'
# ==========================================

jumlah_lulus2 = df.filter(
    col("status_mahasiswa") == "Lulus"
).count()

print(f"Jumlah status = 'Lulus' : {jumlah_lulus2}")

# ==========================================
# Cek filter 'AKTIF'
# ==========================================

jumlah_aktif = df.filter(
    col("status_mahasiswa") == "AKTIF"
).count()

print(f"Jumlah status = 'AKTIF' : {jumlah_aktif}")

# ==========================================
# Cek Missing Value estimasi_semester
# ==========================================

jumlah_null = df.filter(
    col("estimasi_semester").isNull()
).count()

print(f"\nNULL estimasi_semester : {jumlah_null}")

# ==========================================
# Tampilkan contoh data
# ==========================================

print("\nContoh Data")
df.select(
    "status_mahasiswa",
    "estimasi_semester",
    "tanggal_masuk",
    "tanggal_keluar"
).show(20, truncate=False)

spark.stop()