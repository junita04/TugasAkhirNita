from backend.spark.session import get_spark
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_gold_kurikulum():

    spark = get_spark("Gold Kurikulum")

    logger.info("=" * 60)
    logger.info("Membuat Gold Kurikulum")

    # ===============================
    # Membaca Silver Layer
    # ===============================

    df = spark.table("local.silver.data_kurikulum")

    logger.info(f"Jumlah Data : {df.count()}")

    # ===============================
    # Menyimpan ke Gold Layer
    # ===============================

    (
        df.writeTo("local.gold.gold_kurikulum")
        .using("iceberg")
        .createOrReplace()
    )

    logger.info("Gold Kurikulum berhasil dibuat.")

    return df