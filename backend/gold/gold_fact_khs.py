from pyspark.sql import functions as F

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

GOLD_TABLE_FACT = f"{ICEBERG_NAMESPACE}.gold.fact_khs"
GOLD_TABLE_FACT_HIVE = "hive_iceberg.gold.fact_khs"

# Grain: 1 baris = 1 mahasiswa (satu IP + satu SKS per mahasiswa).
FACT_KHS_COLUMNS = ["id_mahasiswa", "ip", "sks", "jumlah_data_khs"]


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
    # Agregasi per mahasiswa: IP, SKS, jumlah data KHS
    # Grain: 1 id_mahasiswa = 1 baris
    # =====================================================

    df = df.groupBy("id_mahasiswa").agg(
        F.first("ip", ignorenulls=True).alias("ip"),
        F.first("sks", ignorenulls=True).alias("sks"),
        F.count("*").alias("jumlah_data_khs"),
    )

    logger.info(f"Rows fact (setelah groupBy id_mahasiswa) : {df.count()}")

    # =====================================================
    # Simpan Gold (Iceberg, catalog ICEBERG_NAMESPACE)
    # =====================================================

    (
        df.writeTo(GOLD_TABLE_FACT)
        .using("iceberg")
        .createOrReplace()
    )

    # Write to HMS-backed catalog for Trino visibility
    (
        df.writeTo(GOLD_TABLE_FACT_HIVE)
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
