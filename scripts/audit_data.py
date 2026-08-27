"""
DATA AUDIT — Bronze → Silver → Gold → Feature Store
Fokus: Mahasiswa Angkatan 2023 dengan status Lulus

READ-ONLY. Tidak ada perubahan data.
"""

import warnings
warnings.filterwarnings("ignore")

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

print("=" * 70)
print("DATA AUDIT — BRONZE → SILVER → GOLD → FEATURE STORE")
print("READ-ONLY — Tidak ada perubahan data")
print("=" * 70)

# ============================================================
# INITIALIZE SPARK
# ============================================================
spark = (
    SparkSession.builder
    .appName("TA_Audit_Bronze_Silver_Gold")
    .master("local[*]")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3.path.style.access", "true")
    .config("spark.hadoop.fs.s3.connection.ssl.enabled", "false")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hive")
    .config("spark.sql.catalog.iceberg.uri", "thrift://hive-metastore:9083")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.driver.memory", "2g")
    .config("spark.eventLog.enabled", "true")
    .config("spark.eventLog.dir", "file:///spark-events")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")
print(f"Application ID: {spark.sparkContext.applicationId}")

# ============================================================
# STEP 1: IDENTIFIKASI DATABASE DAN TABEL
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: IDENTIFIKASI DATABASE DAN TABEL")
print("=" * 70)

print("\n--- SHOW DATABASES ---")
databases = spark.sql("SHOW DATABASES").collect()
for row in databases:
    print(f"  {row[0]}")

print("\n--- SHOW TABLES IN iceberg.bronze ---")
try:
    bronze_tables = spark.sql("SHOW TABLES IN iceberg.bronze").collect()
    for row in bronze_tables:
        print(f"  {row[1]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n--- SHOW TABLES IN iceberg.silver ---")
try:
    silver_tables = spark.sql("SHOW TABLES IN iceberg.silver").collect()
    for row in silver_tables:
        print(f"  {row[1]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n--- SHOW TABLES IN iceberg.gold ---")
try:
    gold_tables = spark.sql("SHOW TABLES IN iceberg.gold").collect()
    for row in gold_tables:
        print(f"  {row[1]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n--- SHOW TABLES IN iceberg.feature_store ---")
try:
    fs_tables = spark.sql("SHOW TABLES IN iceberg.feature_store").collect()
    for row in fs_tables:
        print(f"  {row[1]}")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# STEP 2: AUDIT BRONZE
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: AUDIT BRONZE")
print("=" * 70)

bronze_table = "iceberg.bronze.data_referensi_mahasiswa"
print(f"\nTable: {bronze_table}")

df_bronze = spark.table(bronze_table)
print(f"Total rows: {df_bronze.count()}")

print("\nSchema:")
df_bronze.printSchema()

print("\n--- Angkatan 2023 Analysis (derived from tanggal_masuk) ---")
# Bronze doesn't have 'angkatan' column, derive from tanggal_masuk
print("Note: Bronze does NOT have 'angkatan' column. Deriving from tanggal_masuk.")

bronze_2023 = df_bronze.filter(
    (F.year(F.col("tanggal_masuk")) == 2023) |
    (F.col("tanggal_masuk").contains("2023"))
)

count_2023 = bronze_2023.count()
print(f"\nBronze - Mahasiswa dengan tanggal_masuk tahun 2023: {count_2023}")

if count_2023 > 0:
    print("\nDistribusi status mahasiswa (angkatan 2023):")
    bronze_2023.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

    print("\n--- Cek apakah ada Lulus ---")
    bronze_2023_lulus = bronze_2023.filter(F.col("status_mahasiswa") == "Lulus")
    count_lulus = bronze_2023_lulus.count()
    print(f"Bronze - Mahasiswa angkatan 2023 dengan status Lulus: {count_lulus}")

    if count_lulus > 0:
        print("\n*** BRONZE: DITEMUKAN mahasiswa angkatan 2023 dengan status Lulus! ***")
        bronze_2023_lulus.select(
            "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
            "ipk", "total_sks", "jumlah_mk"
        ).show(10, truncate=False)
    else:
        print("\nBRONZE: Tidak ditemukan mahasiswa angkatan 2023 dengan status Lulus.")
else:
    print("\nTidak ada mahasiswa dengan tanggal_masuk tahun 2023.")

print("\n--- All status_mahasiswa distribution ---")
df_bronze.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

print("\n--- Cek tanggal_masuk NULL ---")
null_tanggal = df_bronze.filter(F.col("tanggal_masuk").isNull()).count()
print(f"Bronze - tanggal_masuk NULL: {null_tanggal}")

print("\n--- Sample data tahun 2023 (tanggal_masuk contains '2023') ---")
sample_2023 = df_bronze.filter(F.col("tanggal_masuk").cast("string").contains("2023"))
print(f"Rows with tanggal_masuk containing '2023': {sample_2023.count()}")
if sample_2023.count() > 0:
    sample_2023.select(
        "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
        "ipk", "total_sks"
    ).show(20, truncate=False)

# ============================================================
# STEP 3: AUDIT SILVER
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: AUDIT SILVER")
print("=" * 70)

silver_table = "iceberg.silver.data_referensi_mahasiswa"
print(f"\nTable: {silver_table}")

df_silver = spark.table(silver_table)
print(f"Total rows: {df_silver.count()}")

print("\nSchema:")
df_silver.printSchema()

print("\n--- Angkatan 2023 Analysis (derived from tanggal_masuk) ---")
silver_2023 = df_silver.filter(
    (F.year(F.col("tanggal_masuk")) == 2023) |
    (F.col("tanggal_masuk").contains("2023"))
)

count_silver_2023 = silver_2023.count()
print(f"Silver - Mahasiswa dengan tanggal_masuk tahun 2023: {count_silver_2023}")

if count_silver_2023 > 0:
    print("\nDistribusi status mahasiswa (angkatan 2023):")
    silver_2023.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

    print("\n--- Cek apakah ada Lulus ---")
    silver_2023_lulus = silver_2023.filter(F.col("status_mahasiswa") == "Lulus")
    count_silver_lulus = silver_2023_lulus.count()
    print(f"Silver - Mahasiswa angkatan 2023 dengan status Lulus: {count_silver_lulus}")

    if count_silver_lulus > 0:
        print("\n*** SILVER: DITEMUKAN mahasiswa angkatan 2023 dengan status Lulus! ***")
        silver_2023_lulus.select(
            "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
            "ipk", "total_sks", "jumlah_mk"
        ).show(10, truncate=False)
    else:
        print("\nSILVER: Tidak ditemukan mahasiswa angkatan 2023 dengan status Lulus.")
else:
    print("\nTidak ada mahasiswa dengan tanggal_masuk tahun 2023.")

print("\n--- All status_mahasiswa distribution ---")
df_silver.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

# Compare Bronze vs Silver for angkatan 2023
print("\n--- Perbandingan Bronze vs Silver (angkatan 2023) ---")
if count_2023 > 0 and count_silver_2023 > 0:
    bronze_ids_2023 = set([row.id_mhs for row in bronze_2023.select("id_mhs").collect()])
    silver_ids_2023 = set([row.id_mhs for row in silver_2023.select("id_mhs").collect()])

    only_bronze = bronze_ids_2023 - silver_ids_2023
    only_silver = silver_ids_2023 - bronze_ids_2023
    both = bronze_ids_2023 & silver_ids_2023

    print(f"  IDs in Bronze only (removed in Silver): {len(only_bronze)}")
    if only_bronze:
        print(f"    {list(only_bronze)[:10]}")

    print(f"  IDs in Silver only (added in Silver): {len(only_silver)}")
    if only_silver:
        print(f"    {list(only_silver)[:10]}")

    print(f"  IDs in both: {len(both)}")

# ============================================================
# STEP 4: AUDIT GOLD
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: AUDIT GOLD")
print("=" * 70)

gold_table = "iceberg.gold.data_referensi_mahasiswa"
print(f"\nTable: {gold_table}")

df_gold = spark.table(gold_table)
print(f"Total rows: {df_gold.count()}")

print("\nSchema:")
df_gold.printSchema()

print("\n--- Gold has 'angkatan' column (derived in feature engineering) ---")
gold_2023 = df_gold.filter(F.col("angkatan") == 2023)
count_gold_2023 = gold_2023.count()
print(f"Gold - Mahasiswa angkatan 2023: {count_gold_2023}")

if count_gold_2023 > 0:
    print("\nDistribusi status mahasiswa (angkatan 2023):")
    gold_2023.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

    print("\n--- Cek apakah ada Lulus ---")
    gold_2023_lulus = gold_2023.filter(F.col("status_mahasiswa") == "Lulus")
    count_gold_lulus = gold_2023_lulus.count()
    print(f"Gold - Mahasiswa angkatan 2023 dengan status Lulus: {count_gold_lulus}")

    if count_gold_lulus > 0:
        print("\n*** GOLD: DITEMUKAN mahasiswa angkatan 2023 dengan status Lulus! ***")
        gold_2023_lulus.select(
            "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
            "angkatan", "semester", "ipk", "total_sks", "jumlah_mk",
            "target_sks_kumulatif", "selisih_sks", "status_kelulusan"
        ).show(10, truncate=False)

        # Show status_kelulusan for these students
        print("\nStatus kelulusan mahasiswa angkatan 2023 Lulus:")
        gold_2023_lulus.groupBy("status_kelulusan").count().show()
    else:
        print("\nGOLD: Tidak ditemukan mahasiswa angkatan 2023 dengan status Lulus.")
else:
    print("\nTidak ada mahasiswa angkatan 2023.")

print("\n--- All status_mahasiswa distribution ---")
df_gold.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

print("\n--- status_kelulusan distribution (all) ---")
df_gold.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).show()

print("\n--- angkatan distribution ---")
df_gold.groupBy("angkatan").count().orderBy("angkatan").show(20, truncate=False)

# ============================================================
# STEP 5: TRACE 3 MAHASISWA ANGKATAN 2023
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: TRACE 3 MAHASISWA ANGKATAN 2023")
print("=" * 70)

# First find them in Feature Store
fs_table = "iceberg.feature_store.feature_store_graduation_prediction"
df_fs = spark.table(fs_table)

fs_2023 = df_fs.filter(F.col("angkatan") == 2023)
count_fs_2023 = fs_2023.count()
print(f"\nFeature Store - Mahasiswa angkatan 2023: {count_fs_2023}")

if count_fs_2023 > 0:
    print("\n--- Daftar mahasiswa angkatan 2023 di Feature Store ---")
    fs_2023.select(
        "id_mhs", "jenis_kelamin", "ipk", "total_sks", "jumlah_mk",
        "angkatan", "semester", "target_sks_kumulatif", "selisih_sks",
        "status_kelulusan"
    ).show(20, truncate=False)

    # Get IDs
    ids_2023 = [row.id_mhs for row in fs_2023.select("id_mhs").collect()]
    print(f"ID mahasiswa angkatan 2023: {ids_2023}")

    # Trace each ID through all layers
    for mid in ids_2023:
        print(f"\n{'='*60}")
        print(f"TRACE: {mid}")
        print(f"{'='*60}")

        # Feature Store
        fs_row = df_fs.filter(F.col("id_mhs") == mid)
        print(f"\n[FEATURE STORE]")
        fs_row.show(1, truncate=False)

        # Gold
        gold_row = df_gold.filter(F.col("id_mhs") == mid)
        print(f"[GOLD] rows found: {gold_row.count()}")
        if gold_row.count() > 0:
            gold_row.select(
                "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
                "angkatan", "semester", "ipk", "total_sks", "jumlah_mk",
                "target_sks_kumulatif", "selisih_sks", "status_kelulusan"
            ).show(1, truncate=False)

        # Silver
        silver_row = df_silver.filter(F.col("id_mhs") == mid)
        print(f"[SILVER] rows found: {silver_row.count()}")
        if silver_row.count() > 0:
            silver_row.select(
                "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
                "ipk", "total_sks", "jumlah_mk"
            ).show(1, truncate=False)

        # Bronze
        bronze_row = df_bronze.filter(F.col("id_mhs") == mid)
        print(f"[BRONZE] rows found: {bronze_row.count()}")
        if bronze_row.count() > 0:
            bronze_row.select(
                "id_mhs", "tanggal_masuk", "tanggal_keluar", "status_mahasiswa",
                "ipk", "total_sks", "jumlah_mk"
            ).show(1, truncate=False)
else:
    print("\nTidak ditemukan mahasiswa angkatan 2023 di Feature Store.")

# ============================================================
# STEP 6: CEK CARA MENGHITUNG ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: CEK CARA MENGHITUNG ANGKATAN")
print("=" * 70)

print("""
Gold feature engineering logic (from create_gold.py):
  angkatan = year(tanggal_masuk)

Contoh:
  tanggal_masuk = 2023-08-15 → angkatan = 2023
  tanggal_masuk = 2022-08-15 → angkatan = 2022
""")

print("--- Validasi angkatan dari tanggal_masuk di Gold ---")
gold_angkatan_check = df_gold.select(
    "id_mhs", "tanggal_masuk", "angkatan"
).withColumn(
    "year_from_tanggal", F.year(F.col("tanggal_masuk"))
).withColumn(
    "match", F.col("angkatan") == F.col("year_from_tanggal")
)

mismatch = gold_angkatan_check.filter(F.col("match") == False).count()
print(f"Angkatan mismatch (angkatan != year(tanggal_masuk)): {mismatch}")

if mismatch > 0:
    print("\nMismatched records:")
    gold_angkatan_check.filter(F.col("match") == False).show(20, truncate=False)

# Check for NULL tanggal_masuk
null_tanggal_gold = df_gold.filter(F.col("tanggal_masuk").isNull()).count()
print(f"\nGold - tanggal_masuk NULL: {null_tanggal_gold}")

# ============================================================
# STEP 7: CEK STATUS KELULUSAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: CEK STATUS KELULUSAN")
print("=" * 70)

print("""
Gold feature engineering logic (from create_gold.py):
  if status_mahasiswa == 'Lulus':
    if lama_studi <= 4.5: status_kelulusan = 'Tepat Waktu'
    else: status_kelulusan = 'Terlambat'
  else:
    status_kelulusan = NULL
""")

# ============================================================
# STEP 8: VALIDASI LABEL
# ============================================================
print("\n" + "=" * 70)
print("STEP 8: VALIDASI LABEL")
print("=" * 70)

print("\n--- Tabel Validasi: status_mahasiswa × status_kelulusan ---")
label_check = df_gold.groupBy("status_mahasiswa", "status_kelulusan").count().orderBy("status_mahasiswa", "status_kelulusan")
label_check.show(20, truncate=False)

# Check for leakage: non-Lulus students with status_kelulusan
print("\n--- Cek Data Leakage: Non-Lulus dengan status_kelulusan TIDAK NULL ---")
leakage = df_gold.filter(
    (F.col("status_mahasiswa") != "Lulus") &
    (F.col("status_kelulusan").isNotNull())
)
leakage_count = leakage.count()
print(f"Non-Lulus dengan status_kelulusan TIDAK NULL: {leakage_count}")

if leakage_count > 0:
    print("\n*** POTENSI DATA LEAKAGE! ***")
    leakage.select(
        "id_mhs", "status_mahasiswa", "angkatan", "status_kelulusan"
    ).show(20, truncate=False)

# ============================================================
# STEP 9: VALIDASI ANGKATAN 2023
# ============================================================
print("\n" + "=" * 70)
print("STEP 9: VALIDASI ANGKATAN 2023 — RINGKASAN")
print("=" * 70)

print("\n--- Ringkasan per Layer ---")
print(f"{'Layer':<20} {'Total A2023':>12} {'Lulus':>8} {'Aktif':>8} {'Lain':>8} {'Keterangan'}")
print("-" * 80)

# Bronze (derive from tanggal_masuk)
b_2023_all = df_bronze.filter(F.year(F.col("tanggal_masuk")) == 2023)
b_total = b_2023_all.count()
b_lulus = b_2023_all.filter(F.col("status_mahasiswa") == "Lulus").count()
b_aktif = b_2023_all.filter(F.col("status_mahasiswa") == "AKTIF").count()
b_lain = b_total - b_lulus - b_aktif
print(f"{'Bronze':<20} {b_total:>12} {b_lulus:>8} {b_aktif:>8} {b_lain:>8} Derive from tanggal_masuk")

# Silver
s_2023_all = df_silver.filter(F.year(F.col("tanggal_masuk")) == 2023)
s_total = s_2023_all.count()
s_lulus = s_2023_all.filter(F.col("status_mahasiswa") == "Lulus").count()
s_aktif = s_2023_all.filter(F.col("status_mahasiswa") == "AKTIF").count()
s_lain = s_total - s_lulus - s_aktif
print(f"{'Silver':<20} {s_total:>12} {s_lulus:>8} {s_aktif:>8} {s_lain:>8} Derive from tanggal_masuk")

# Gold
g_2023_all = df_gold.filter(F.col("angkatan") == 2023)
g_total = g_2023_all.count()
g_lulus = g_2023_all.filter(F.col("status_mahasiswa") == "Lulus").count()
g_aktif = g_2023_all.filter(F.col("status_mahasiswa") == "AKTIF").count()
g_lain = g_total - g_lulus - g_aktif
print(f"{'Gold':<20} {g_total:>12} {g_lulus:>8} {g_aktif:>8} {g_lain:>8} angkatan column")

# Feature Store
fs_2023_all = df_fs.filter(F.col("angkatan") == 2023)
fs_total = fs_2023_all.count()
fs_lulus_tw = fs_2023_all.filter(F.col("status_kelulusan") == "Tepat Waktu").count()
fs_lulus_tl = fs_2023_all.filter(F.col("status_kelulusan") == "Terlambat").count()
fs_other = fs_total - fs_lulus_tw - fs_lulus_tl
print(f"{'Feature Store':<20} {fs_total:>12} {fs_lulus_tw:>8} {'':>8} {fs_lulus_tl:>8} Filter: Lulus only")
print(f"{'  (TW/TL)':<20} {'':>12} {fs_lulus_tw:>8} {'':>8} {fs_lulus_tl:>8} TW=TW, TL=TL")

# ============================================================
# KESIMPULAN
# ============================================================
print("\n" + "=" * 70)
print("KESIMPULAN AUDIT")
print("=" * 70)

# Check if angkatan 2023 exists in any layer with Lulus
print(f"""
Bronze: {b_lulus} mahasiswa angkatan 2023 dengan status Lulus
Silver: {s_lulus} mahasiswa angkatan 2023 dengan status Lulus
Gold:   {g_lulus} mahasiswa angkatan 2023 dengan status Lulus
Feature Store: {fs_lulus_tw + fs_lulus_tl} mahasiswa angkatan 2023 (TW={fs_lulus_tw}, TL={fs_lulus_tl})
""")

if b_lulus == 0 and s_lulus == 0 and g_lulus == 0 and (fs_lulus_tw + fs_lulus_tl) > 0:
    print("*** ROOT CAUSE: Ketidaksesuaian berasal dari tahap GOLD → FEATURE STORE ***")
    print("    Gold tidak memiliki mahasiswa angkatan 2023 Lulus,")
    print("    tetapi Feature Store memiliki 3 mahasiswa angkatan 2023.")
elif b_lulus > 0:
    print(f"*** ROOT CAUSE: Masalah berasal dari tahap BRONZE ***")
    print(f"    Bronze memiliki {b_lulus} mahasiswa angkatan 2023 dengan status Lulus.")
elif s_lulus > 0 and b_lulus == 0:
    print(f"*** ROOT CAUSE: Masalah berasal dari tahap SILVER → GOLD ***")
    print(f"    Silver memiliki {s_lulus} mahasiswa angkatan 2023 Lulus,")
    print(f"    tetapi Bronze tidak memiliki.")
elif g_lulus > 0 and s_lulus == 0:
    print(f"*** ROOT CAUSE: Masalah berasal dari tahap GOLD ***")
    print(f"    Gold memiliki {g_lulus} mahasiswa angkatan 2023 Lulus,")
    print(f"    tetapi Silver tidak memiliki.")
elif b_lulus == 0 and s_lulus == 0 and g_lulus == 0 and (fs_lulus_tw + fs_lulus_tl) == 0:
    print("Tidak ditemukan masalah. Tidak ada mahasiswa angkatan 2023 dengan status Lulus di semua layer.")
else:
    print("Perlu analisis lebih lanjut.")

# ============================================================
# FINAL: Show all angkatan 2023 data in Feature Store
# ============================================================
print("\n" + "=" * 70)
print("SEMUA DATA ANGKATAN 2023 DI FEATURE STORE")
print("=" * 70)

if count_fs_2023 > 0:
    fs_2023.select(
        "id_mhs", "jenis_kelamin", "ipk", "total_sks", "jumlah_mk",
        "angkatan", "semester", "target_sks_kumulatif", "selisih_sks",
        "status_kelulusan"
    ).show(20, truncate=False)
else:
    print("Tidak ada data angkatan 2023 di Feature Store.")

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)

spark.stop()
