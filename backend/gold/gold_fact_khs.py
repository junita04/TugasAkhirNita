from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

GOLD_TABLE_FACT = f"{ICEBERG_NAMESPACE}.gold.fact_khs"

# Grain: 1 baris = 1 mahasiswa (satu IP + satu SKS per mahasiswa).
FACT_KHS_COLUMNS = ["id_mahasiswa", "ip", "sks"]


def process_gold_fact_khs():

    spark = get_spark("TugasAkhirNita - Gold Fact KHS")

    logger.info("=" * 60)
    logger.info("MEMBUAT GOLD FACT_KHS (STAR SCHEMA)")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Silver Layer (sumber Gold HANYA dari Silver)
    # =====================================================

    df = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_khs")

    logger.info(f"Rows Silver silver_khs : {df.count()}")

    # =====================================================
    # Pilih kolom fact + jamin grain 1 mahasiswa = 1 row
    # =====================================================

    df = df.select(*FACT_KHS_COLUMNS)

    df = df.dropDuplicates(["id_mahasiswa"])

    logger.info(f"Rows fact (setelah dedup id_mahasiswa) : {df.count()}")

    # =====================================================
    # Simpan Gold (Iceberg, catalog ICEBERG_NAMESPACE)
    # =====================================================

    (
        df.writeTo(GOLD_TABLE_FACT)
        .using("iceberg")
        .createOrReplace()
    )

    spark.sql(
        f"ALTER TABLE {GOLD_TABLE_FACT} SET TBLPROPERTIES ('comment' = "
        f"'Star Schema Fact - Foreign Key: id_mahasiswa -> dim_mahasiswa "
        f"(1 baris = 1 mahasiswa)')"
    )

    logger.info(f"Rows Gold Tersimpan : {df.count()}")
    logger.info("✓ Gold fact_khs berhasil dibuat.")
    logger.info("=" * 60)

    return df