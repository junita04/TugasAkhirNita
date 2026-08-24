from pyspark.sql import functions as F

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

GOLD_TABLE_DIM = f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa"

# Atribut dim_mahasiswa (Plain data Gold, tanpa feature engineering).
DIM_MAHASISWA_COLUMNS = [
    "id_mahasiswa",
    "jenis_kelamin",
    "tanggal_masuk",
    "tanggal_keluar",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "status_mahasiswa",
]


def process_gold_dim_mahasiswa():

    spark = get_spark("TugasAkhirNita - Gold Dim Mahasiswa")

    logger.info("=" * 60)
    logger.info("MEMBUAT GOLD DIM_MAHASISWA (STAR SCHEMA)")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Silver Layer (sumber Gold HANYA dari Silver)
    # =====================================================

    df = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa")

    logger.info(f"Rows Silver silver_mahasiswa : {df.count()}")

    # =====================================================
    # Pilih atribut saja + jamin grain 1 mahasiswa = 1 row
    # =====================================================

    df = df.select(*DIM_MAHASISWA_COLUMNS)

    df = df.dropDuplicates(["id_mahasiswa"])

    logger.info(f"Rows dim (setelah dedup id_mahasiswa) : {df.count()}")

    # =====================================================
    # Simpan Gold (Iceberg, catalog ICEBERG_NAMESPACE)
    # =====================================================

    (
        df.writeTo(GOLD_TABLE_DIM)
        .using("iceberg")
        .createOrReplace()
    )

    spark.sql(
        f"ALTER TABLE {GOLD_TABLE_DIM} SET TBLPROPERTIES ('comment' = "
        f"'Star Schema Dimension - Primary Key: id_mahasiswa (1 baris = 1 mahasiswa)')"
    )

    logger.info(f"Rows Gold Tersimpan : {df.count()}")
    logger.info("✓ Gold dim_mahasiswa berhasil dibuat.")
    logger.info("=" * 60)

    return df