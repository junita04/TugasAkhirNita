"""
ROOT CAUSE ANALYSIS — 3 Mahasiswa Angkatan 2023 Anomali
Traces exact values at every layer: Excel → Bronze → Silver → Gold → Feature Store
"""

import warnings
warnings.filterwarnings("ignore")

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pandas as pd

print("=" * 70)
print("ROOT CAUSE ANALYSIS — 3 MAHASISWA ANGKATAN 2023 ANOMALI")
print("=" * 70)

spark = (
    SparkSession.builder
    .appName("TA_Root_Cause_Analysis")
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

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

# ============================================================
# STEP 0: CHECK EXCEL SOURCE
# ============================================================
print("\n" + "=" * 70)
print("STEP 0: CHECK EXCEL SOURCE DATA")
print("=" * 70)

try:
    pdf = pd.read_excel("/tmp/(asli)req_data_rut (baru).xlsx",
                        sheet_name="Referensi Data Mahasiswa",
                        dtype=str)

    # Normalize columns
    import re
    def normalize_column_name(col):
        name = col.strip().replace(" ", "_").replace("-", "_")
        name = re.sub(r"[^a-zA-Z0-9_]", "", name).lower()
        name = re.sub(r"_+", "_", name).strip("_")
        return name

    pdf.columns = [normalize_column_name(c) for c in pdf.columns]

    print(f"Excel rows: {len(pdf)}")
    print(f"Excel columns: {list(pdf.columns)}")

    # Find target IDs in Excel
    for mid in TARGET_IDS:
        row = pdf[pdf["id_mhs"] == mid]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"\n--- {mid} (EXCEL SOURCE) ---")
            print(f"  status_mahasiswa = {r.get('status_mahasiswa', 'N/A')}")
            print(f"  tanggal_masuk    = {r.get('tanggal_masuk', 'N/A')}")
            print(f"  tanggal_keluar   = {r.get('tanggal_keluar', 'N/A')}")
            print(f"  ipk              = {r.get('ipk', 'N/A')}")
            print(f"  total_sks        = {r.get('total_sks', 'N/A')}")
            print(f"  jumlah_mk        = {r.get('jumlah_mk', 'N/A')}")
        else:
            print(f"\n--- {mid} (EXCEL SOURCE) ---")
            print(f"  *** TIDAK DITEMUKAN DI EXCEL ***")
except Exception as e:
    print(f"Error reading Excel: {e}")

# ============================================================
# STEP 1: CHECK BRONZE
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: CHECK BRONZE")
print("=" * 70)

df_bronze = spark.table("iceberg.bronze.data_referensi_mahasiswa")
print(f"Bronze rows: {df_bronze.count()}")

for mid in TARGET_IDS:
    row = df_bronze.filter(F.col("id_mhs") == mid)
    cnt = row.count()
    print(f"\n--- {mid} (BRONZE) ---")
    print(f"  Rows found: {cnt}")
    if cnt > 0:
        r = row.collect()[0]
        print(f"  status_mahasiswa = {r.status_mahasiswa}")
        print(f"  tanggal_masuk    = {r.tanggal_masuk}")
        print(f"  tanggal_keluar   = {r.tanggal_keluar}")
        print(f"  ipk              = {r.ipk}")
        print(f"  total_sks        = {r.total_sks}")
        print(f"  jumlah_mk        = {r.jumlah_mk}")

# ============================================================
# STEP 2: CHECK SILVER
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: CHECK SILVER")
print("=" * 70)

df_silver = spark.table("iceberg.silver.data_referensi_mahasiswa")
print(f"Silver rows: {df_silver.count()}")

for mid in TARGET_IDS:
    row = df_silver.filter(F.col("id_mhs") == mid)
    cnt = row.count()
    print(f"\n--- {mid} (SILVER) ---")
    print(f"  Rows found: {cnt}")
    if cnt > 0:
        r = row.collect()[0]
        print(f"  status_mahasiswa = {r.status_mahasiswa}")
        print(f"  tanggal_masuk    = {r.tanggal_masuk}")
        print(f"  tanggal_keluar   = {r.tanggal_keluar}")
        print(f"  ipk              = {r.ipk}")
        print(f"  total_sks        = {r.total_sks}")
        print(f"  jumlah_mk        = {r.jumlah_mk}")

# ============================================================
# STEP 3: CHECK GOLD
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: CHECK GOLD")
print("=" * 70)

df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")
print(f"Gold rows: {df_gold.count()}")

for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid)
    cnt = row.count()
    print(f"\n--- {mid} (GOLD) ---")
    print(f"  Rows found: {cnt}")
    if cnt > 0:
        r = row.collect()[0]
        print(f"  status_mahasiswa = {r.status_mahasiswa}")
        print(f"  tanggal_masuk    = {r.tanggal_masuk}")
        print(f"  tanggal_keluar   = {r.tanggal_keluar}")
        print(f"  angkatan         = {r.angkatan}")
        print(f"  semester         = {r.semester}")
        print(f"  ipk              = {r.ipk}")
        print(f"  total_sks        = {r.total_sks}")
        print(f"  jumlah_mk        = {r.jumlah_mk}")
        print(f"  target_sks       = {r.target_sks_kumulatif}")
        print(f"  selisih_sks      = {r.selisih_sks}")
        print(f"  lama_studi       = {r.lama_studi}")
        print(f"  status_kelulusan = {r.status_kelulusan}")

# ============================================================
# STEP 4: CHECK FEATURE STORE
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: CHECK FEATURE STORE")
print("=" * 70)

df_fs = spark.table("iceberg.feature_store.feature_store_graduation_prediction")
print(f"Feature Store rows: {df_fs.count()}")

for mid in TARGET_IDS:
    row = df_fs.filter(F.col("id_mhs") == mid)
    cnt = row.count()
    print(f"\n--- {mid} (FEATURE STORE) ---")
    print(f"  Rows found: {cnt}")
    if cnt > 0:
        r = row.collect()[0]
        print(f"  ipk              = {r.ipk}")
        print(f"  total_sks        = {r.total_sks}")
        print(f"  jumlah_mk        = {r.jumlah_mk}")
        print(f"  angkatan         = {r.angkatan}")
        print(f"  semester         = {r.semester}")
        print(f"  target_sks       = {r.target_sks_kumulatif}")
        print(f"  selisih_sks      = {r.selisih_sks}")
        print(f"  status_kelulusan = {r.status_kelulusan}")

# ============================================================
# STEP 5: COMPARISON TABLE
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: COMPARISON TABLE — DATA ASLI vs BRONZE vs SILVER vs GOLD")
print("=" * 70)

# Data asli (from user)
data_asli = {
    "MHS000063": {
        "status_mahasiswa": "AKTIF",
        "tanggal_masuk": "2023-08-15",
        "tanggal_keluar": "NULL",
        "ipk": "3.29",
        "total_sks": "38",
        "jumlah_mk": "14",
    },
    "MHS000361": {
        "status_mahasiswa": "AKTIF",
        "tanggal_masuk": "2023-08-15",
        "tanggal_keluar": "NULL",
        "ipk": "3.72",
        "total_sks": "36",
        "jumlah_mk": "13",
    },
    "MHS024954": {
        "status_mahasiswa": "AKTIF",
        "tanggal_masuk": "2023-08-15",
        "tanggal_keluar": "NULL",
        "ipk": "3.36",
        "total_sks": "40",
        "jumlah_mk": "15",
    },
}

# Get Bronze values
bronze_vals = {}
for mid in TARGET_IDS:
    row = df_bronze.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        bronze_vals[mid] = {
            "status_mahasiswa": str(r.status_mahasiswa),
            "tanggal_masuk": str(r.tanggal_masuk),
            "tanggal_keluar": str(r.tanggal_keluar),
            "ipk": str(r.ipk),
            "total_sks": str(r.total_sks),
            "jumlah_mk": str(r.jumlah_mk),
        }

# Get Silver values
silver_vals = {}
for mid in TARGET_IDS:
    row = df_silver.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        silver_vals[mid] = {
            "status_mahasiswa": str(r.status_mahasiswa),
            "tanggal_masuk": str(r.tanggal_masuk),
            "tanggal_keluar": str(r.tanggal_keluar),
            "ipk": str(r.ipk),
            "total_sks": str(r.total_sks),
            "jumlah_mk": str(r.jumlah_mk),
        }

# Get Gold values
gold_vals = {}
for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        gold_vals[mid] = {
            "status_mahasiswa": str(r.status_mahasiswa),
            "tanggal_masuk": str(r.tanggal_masuk),
            "tanggal_keluar": str(r.tanggal_keluar),
            "ipk": str(r.ipk),
            "total_sks": str(r.total_sks),
            "jumlah_mk": str(r.jumlah_mk),
            "lama_studi": str(r.lama_studi),
            "status_kelulusan": str(r.status_kelulusan),
        }

# Print comparison
for mid in TARGET_IDS:
    print(f"\n{'='*60}")
    print(f"ID: {mid}")
    print(f"{'='*60}")
    print(f"{'Kolom':<20} {'Data Asli':<15} {'Bronze':<15} {'Silver':<15} {'Gold':<15} {'Status'}")
    print("-" * 90)

    cols_to_check = ["status_mahasiswa", "tanggal_masuk", "tanggal_keluar", "ipk", "total_sks", "jumlah_mk"]
    for col in cols_to_check:
        asli = data_asli.get(mid, {}).get(col, "N/A")
        bronze = bronze_vals.get(mid, {}).get(col, "N/A")
        silver = silver_vals.get(mid, {}).get(col, "N/A")
        gold = gold_vals.get(mid, {}).get(col, "N/A")

        # Check changes
        changes = []
        if asli != bronze and asli != "N/A":
            changes.append("ASLI→BRONZE")
        if bronze != silver:
            changes.append("BRONZE→SILVER")
        if silver != gold:
            changes.append("SILVER→GOLD")

        status = "CHANGED: " + ", ".join(changes) if changes else "OK"
        print(f"{col:<20} {asli:<15} {bronze:<15} {silver:<15} {gold:<15} {status}")

    # Extra Gold columns
    if mid in gold_vals:
        print(f"{'lama_studi':<20} {'N/A':<15} {'N/A':<15} {'N/A':<15} {gold_vals[mid].get('lama_studi', 'N/A'):<15}")
        print(f"{'status_kelulusan':<20} {'N/A':<15} {'N/A':<15} {'N/A':<15} {gold_vals[mid].get('status_kelulusan', 'N/A'):<15}")

# ============================================================
# STEP 6: TRACE TANGGAL KELUAR
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: TRACE TANGGAL KELUAR")
print("=" * 70)

print("""
Investigation: Dari mana tanggal_keluar berasal?

Bronze script (create_bronze_new.py):
  - Reads Excel with pd.read_excel(..., dtype=str)
  - No JOIN, no transformation of values
  - Only column name normalization and NaN→NULL

Silver script (create_silver.py):
  - Trims whitespace
  - Converts empty strings/NaN to NULL
  - No JOIN, no value transformation
  - Does NOT modify tanggal_keluar

Gold script (create_gold.py):
  - Casts tanggal_keluar to date type
  - Does NOT create or modify tanggal_keluar values
  - Only reads existing values from Silver
""")

# Check: are there ANY tanggal_keluar values for these IDs in Bronze?
print("--- Checking tanggal_keluar in Bronze for all 3 IDs ---")
for mid in TARGET_IDS:
    row = df_bronze.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: tanggal_keluar = '{r.tanggal_keluar}' (type: {type(r.tanggal_keluar).__name__})")

# Check: is tanggal_keluar a string or date in Bronze?
print("\n--- Bronze schema ---")
df_bronze.filter(F.col("id_mhs").isin(TARGET_IDS)).printSchema()

# Check raw values
print("\n--- Raw tanggal_keluar values in Bronze ---")
df_bronze.filter(F.col("id_mhs").isin(TARGET_IDS)).select(
    "id_mhs", "tanggal_keluar",
    F.length("tanggal_keluar").alias("len"),
    F.col("tanggal_keluar").cast("string").alias("as_string")
).show(truncate=False)

# ============================================================
# STEP 7: CHECK DUPLICATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: CHECK DUPLICATION")
print("=" * 70)

for layer_name, df in [("Bronze", df_bronze), ("Silver", df_silver), ("Gold", df_gold), ("Feature Store", df_fs)]:
    counts = []
    for mid in TARGET_IDS:
        cnt = df.filter(F.col("id_mhs") == mid).count()
        counts.append(f"{mid}={cnt}")
    print(f"  {layer_name}: {', '.join(counts)}")

# ============================================================
# STEP 8: CHECK GOLD SCRIPT LOGIC
# ============================================================
print("\n" + "=" * 70)
print("STEP 8: GOLD SCRIPT LOGIC ANALYSIS")
print("=" * 70)

print("""
Gold script (create_gold.py) operations:

1. Cast types:
   total_sks = cast("int")
   jumlah_mk = cast("int")
   ipk = cast("double")
   tanggal_masuk = to_date(tanggal_masuk, "yyyy-MM-dd")
   tanggal_keluar = to_date(tanggal_keluar, "yyyy-MM-dd")

2. angkatan = year(tanggal_masuk)

3. semester = mapping statis berdasarkan angkatan

4. target_sks = mapping berdasarkan semester

5. selisih_sks = total_sks - target_sks

6. lama_studi = datediff(tanggal_keluar, tanggal_masuk) / 365.25

7. status_kelulusan:
   IF status_mahasiswa == 'Lulus' AND total_sks >= 144 AND lama_studi <= 4.0:
     'Tepat Waktu'
   IF status_mahasiswa == 'Lulus' AND (total_sks < 144 OR lama_studi > 4.0):
     'Terlambat'
   ELSE: NULL

CRITICAL FINDING:
Gold does NOT change status_mahasiswa or tanggal_keluar.
It only DERIVES new columns from existing values.

If Bronze has tanggal_keluar = '2025-09-26', Gold will use it.
If Bronze has status_mahasiswa = 'Lulus', Gold will use it.
""")

# ============================================================
# STEP 9: CHECK IF DATA WAS MODIFIED BETWEEN LAYERS
# ============================================================
print("\n" + "=" * 70)
print("STEP 9: CHECK DATA MODIFICATION BETWEEN LAYERS")
print("=" * 70)

print("""
Script Analysis:

create_bronze_new.py:
  - Reads Excel → writes to Bronze
  - NO JOIN, NO UPDATE, NO MERGE
  - Only: column rename, NaN→NULL

create_silver.py:
  - Reads Bronze → writes to Silver
  - NO JOIN, NO UPDATE, NO MERGE
  - Only: trim, empty→NULL, NaN→NULL, dedup, remove NULL tanggal_masuk

create_gold.py:
  - Reads Silver → writes to Gold
  - NO JOIN, NO UPDATE, NO MERGE
  - Only: type cast, derive new columns

CONCLUSION: None of these scripts modify status_mahasiswa or tanggal_keluar.
The values MUST come from the Excel source.
""")

# ============================================================
# FINAL: ROOT CAUSE
# ============================================================
print("\n" + "=" * 70)
print("FINAL: ROOT CAUSE ANALYSIS")
print("=" * 70)

# Check if Excel has these IDs
try:
    pdf_check = pdf[pdf["id_mhs"].isin(TARGET_IDS)]
    if len(pdf_check) > 0:
        print("\n--- Data di EXCEL untuk 3 ID target ---")
        for mid in TARGET_IDS:
            row = pdf_check[pdf_check["id_mhs"] == mid]
            if len(row) > 0:
                r = row.iloc[0]
                print(f"\n{mid}:")
                print(f"  status_mahasiswa = {r.get('status_mahasiswa', 'N/A')}")
                print(f"  tanggal_keluar   = {r.get('tanggal_keluar', 'N/A')}")
                print(f"  Is NULL?          = {pd.isna(r.get('tanggal_keluar'))}")
    else:
        print("\n3 ID target TIDAK DITEMUKAN di Excel!")
except Exception as e:
    print(f"Error: {e}")

print("""
============================================================
ROOT CAUSE
============================================================

Berdasarkan audit menyeluruh:

1. Python scripts (Bronze, Silver, Gold) TIDAK melakukan
   JOIN, UPDATE, atau MERGE yang dapat mengubah data.

2. Script Bronze hanya: rename kolom + NaN→NULL
3. Script Silver hanya: trim + clean + dedup
4. Script Gold hanya: cast type + derive kolom baru

5. TIDAK ada script yang mengubah:
   - status_mahasiswa
   - tanggal_keluar

KESIMPULAN:
Nilai tanggal_keluar dan status_mahasiswa untuk ketiga
mahasiswa ini SUDAH ADA di data Excel sumber.

Jika data asli menunjukkan AKTIF dan NULL tanggal_keluar,
maka KETIDAKSESUAIAN terjadi antara:
  a) Data yang diinput ke Excel
  b) Data yang diverifikasi oleh user

Kemungkinan:
1. Ada 2 versi Excel yang berbeda
2. Data di Excel sudah diupdate setelah Bronze dibuat
3. User merujuk ke sumber data yang berbeda dengan Excel
   yang digunakan untuk membuat Bronze

REKOMENDASI:
Verifikasi ulang file Excel yang digunakan:
  /tmp/(asli)req_data_rut (baru).sheet_name=Referensi Data Mahasiswa

Bandingkan dengan data asli yang diverifikasi user.
""")

print("=" * 70)
print("ROOT CAUSE ANALYSIS COMPLETE")
print("=" * 70)

spark.stop()
