from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

GOLD_TABLE_DIM_HIVE = "hive_iceberg.gold.dim_mahasiswa"
GOLD_TABLE_DIM = f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa"
GOLD_TABLE_FACT = f"{ICEBERG_NAMESPACE}.gold.fact_khs"
GOLD_TABLE_FACT_HIVE = "hive_iceberg.gold.fact_khs"

# ============================================================
# Target SKS per semester (dari baseline notebook)
# JANGAN gunakan rumus semester × 20.
# ============================================================
TARGET_SKS = {
    1: 17,
    2: 36,
    3: 55,
    4: 75,
    5: 95,
    6: 115,
    7: 135,
    8: 144,
}

# Snapshot semester per angkatan untuk inference 2026
SNAPSHOT_SEMESTER = {
    2022: 7,
    2023: 5,
    2024: 3,
}


def _build_target_sks_case(col_expr):
    """Membangun CASE expression untuk mapping semester -> target SKS."""
    when_expr = F.lit(None).cast(IntegerType())
    for sem, sks in sorted(TARGET_SKS.items()):
        when_expr = F.when(col_expr == sem, sks).otherwise(when_expr)
    return when_expr


def process_gold_dim_mahasiswa():

    spark = get_spark("TugasAkhirNita - Gold Dim Mahasiswa")

    logger.info("=" * 60)
    logger.info("MEMBUAT GOLD DIM_MAHASISWA (STAR SCHEMA WIDE)")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Silver Layer (sumber Gold HANYA dari Silver)
    # =====================================================

    mahasiswa = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa")
    khs = spark.table(GOLD_TABLE_FACT)

    logger.info(f"Rows Silver silver_mahasiswa : {mahasiswa.count()}")
    logger.info(f"Rows Gold fact_khs          : {khs.count()}")

    # =====================================================
    # LEFT JOIN dim_mahasiswa + fact_khs
    # Grain: 1 id_mahasiswa = 1 baris
    # =====================================================

    df = mahasiswa.join(khs, on="id_mahasiswa", how="left")
    df = df.dropDuplicates(["id_mahasiswa"])

    # =====================================================
    # Derive kolom yang dibutuhkan
    # =====================================================

    # angkatan = tahun dari tanggal_masuk
    df = df.withColumn("angkatan", F.year(F.col("tanggal_masuk")))

    # semester: jumlah semester yang telah dilalui dari tanggal_masuk
    # rumus: (bulan sekarang - bulan masuk) / 6 + 1, dibatasi 1-8
    months_elapsed = F.months_between(F.current_date(), F.col("tanggal_masuk"))
    df = df.withColumn(
        "semester_raw",
        F.floor(months_elapsed / F.lit(6)) + F.lit(1),
    )
    df = df.withColumn(
        "semester",
        F.when(F.col("semester_raw") < 1, F.lit(1))
        .when(F.col("semester_raw") > 8, F.lit(8))
        .otherwise(F.col("semester_raw"))
        .cast(IntegerType()),
    )
    df = df.drop("semester_raw")

    # sks_seharusnya berdasarkan mapping TARGET_SKS per semester
    df = df.withColumn(
        "sks_seharusnya",
        _build_target_sks_case(F.col("semester")),
    )

    # selisih_sks = total_sks - sks_seharusnya
    df = df.withColumn(
        "selisih_sks",
        F.col("total_sks") - F.col("sks_seharusnya"),
    )

    # lama_studi (tahun) — hanya untuk LULUS
    df = df.withColumn(
        "lama_studi",
        F.when(
            F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS",
            F.round(
                F.datediff(F.col("tanggal_keluar"), F.col("tanggal_masuk"))
                / F.lit(365),
                2,
            ),
        ),
    )

    # status_kelulusan + label
    df = df.withColumn(
        "status_kelulusan",
        F.when(
            F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS",
            F.when(F.col("lama_studi") <= 4, F.lit("Tepat Waktu")).otherwise(
                F.lit("Terlambat")
            ),
        ).when(
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF")
            & (F.col("angkatan").isin(2019, 2020, 2021)),
            F.lit("Terlambat"),
        ),
    )

    df = df.withColumn(
        "label",
        F.when(F.col("status_kelulusan") == "Tepat Waktu", F.lit(0))
        .when(F.col("status_kelulusan") == "Terlambat", F.lit(1))
        .cast(IntegerType()),
    )

    # =====================================================
    # Simpan Gold (Iceberg, catalog ICEBERG_NAMESPACE)
    # =====================================================

    (
        df.writeTo(GOLD_TABLE_DIM)
        .using("iceberg")
        .createOrReplace()
    )

    # =====================================================
    # Simpan ke HMS-backed catalog untuk Trino visibility
    # =====================================================

    (
        df.writeTo(GOLD_TABLE_DIM_HIVE)
        .using("iceberg")
        .createOrReplace()
    )

    spark.sql(
        f"ALTER TABLE {GOLD_TABLE_DIM} SET TBLPROPERTIES ('comment' = "
        f"'Star Schema Dimension - Primary Key: id_mahasiswa (1 baris = 1 mahasiswa)')"
    )

    final_count = df.count()
    logger.info(f"Rows Gold Tersimpan : {final_count}")
    logger.info("✓ Gold dim_mahasiswa berhasil dibuat (wide schema).")
    logger.info("=" * 60)

    # Validasi kolom wajib
    required = [
        "id_mahasiswa", "jenis_kelamin", "tanggal_masuk", "tanggal_keluar",
        "ipk", "total_sks", "jumlah_mk", "status_mahasiswa",
        "angkatan", "semester", "ip", "sks_seharusnya", "selisih_sks",
        "lama_studi", "status_kelulusan", "label",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.warning(f"Kolom wajib tidak ditemukan: {missing}")
    else:
        logger.info("✓ Semua kolom wajib tersedia.")

    # =====================================================
    # Validasi sks_seharusnya
    # =====================================================

    logger.info("=" * 60)
    logger.info("VALIDASI SKS_SEHARUSNYA")
    logger.info("=" * 60)

    # Validasi: sks_seharusnya harus antara 17 dan 144
    invalid_sks = df.filter(
        (F.col("sks_seharusnya").isNull())
        | (F.col("sks_seharusnya") < 17)
        | (F.col("sks_seharusnya") > 144)
    ).count()

    if invalid_sks > 0:
        logger.warning(f"VALIDASI GAGAL: {invalid_sks} baris memiliki sks_seharusnya di luar rentang 17-144!")
        # Tampilkan contoh data yang invalid
        invalid_samples = df.filter(
            (F.col("sks_seharusnya").isNull())
            | (F.col("sks_seharusnya") < 15)
            | (F.col("sks_seharusnya") > 144)
        ).select("id_mahasiswa", "angkatan", "semester", "sks_seharusnya", "total_sks").limit(5)
        invalid_samples.show()
    else:
        logger.info("✓ sks_seharusnya valid (17-144)")

    # Validasi: selisih_sks = total_sks - sks_seharusnya
    invalid_selisih = df.filter(
        F.col("selisih_sks") != (F.col("total_sks") - F.col("sks_seharusnya"))
    ).count()

    if invalid_selisih > 0:
        logger.warning(f"VALIDASI GAGAL: {invalid_selisih} baris memiliki selisih_sks yang tidak konsisten!")
    else:
        logger.info("✓ selisih_sks konsisten (total_sks - sks_seharusnya)")

    # Distribusi sks_seharusnya
    sks_dist = df.groupBy("sks_seharusnya").count().orderBy("sks_seharusnya").collect()
    logger.info("Distribusi sks_seharusnya:")
    for row in sks_dist:
        logger.info(f"  sks_seharusnya={row['sks_seharusnya']}: {row['count']} baris")

    # Distribusi semester
    sem_dist = df.groupBy("semester").count().orderBy("semester").collect()
    logger.info("Distribusi semester:")
    for row in sem_dist:
        logger.info(f"  semester={row['semester']}: {row['count']} baris")

    return df
