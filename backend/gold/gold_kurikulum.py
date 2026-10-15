from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Katalog HMS-backed agar tabel terlihat oleh Trino
GOLD_CATALOG = "hive_iceberg"


def process_gold_kurikulum():

    spark = get_spark("TugasAkhirNita - Gold Kurikulum")

    logger.info("=" * 60)
    logger.info("Membuat Gold Kurikulum")

    # ===============================
    # Membaca Silver Layer
    # ===============================

    df = spark.table(f"{GOLD_CATALOG}.silver.silver_kurikulum")

    logger.info(f"Jumlah Data : {df.count()}")

    # ===============================
    # Menyimpan ke Gold Layer
    # ===============================

    (
        df.writeTo(f"{GOLD_CATALOG}.gold.gold_kurikulum")
        .using("iceberg")
        .createOrReplace()
    )

    logger.info("Gold Kurikulum berhasil dibuat.")

    return df
