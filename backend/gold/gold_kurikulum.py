from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.config.namespaces import table
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_gold_kurikulum():

    spark = get_spark("TugasAkhirNita - Gold Kurikulum")

    logger.info("=" * 60)
    logger.info("Membuat Gold Kurikulum")

    # ===============================
    # Membaca Silver Layer
    # ===============================

    df = spark.table(table("silver", "silver_kurikulum"))

    logger.info(f"Jumlah Data : {df.count()}")

    # ===============================
    # Menyimpan ke Gold Layer
    # ===============================

    (
        df.writeTo(table("gold", "gold_kurikulum"))
        .using("iceberg")
        .createOrReplace()
    )

    logger.info("Gold Kurikulum berhasil dibuat.")

    return df
