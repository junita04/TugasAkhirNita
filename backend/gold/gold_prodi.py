from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.config.namespaces import table
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_gold_program_studi():

    spark = get_spark("TugasAkhirNita - Gold Prodi")

    logger.info("=" * 60)
    logger.info("Membuat Gold Program Studi")

    # ===============================
    # Membaca Silver Layer
    # ===============================

    df = spark.table(table("silver", "silver_program_studi"))

    logger.info(f"Jumlah Data : {df.count()}")

    # ===============================
    # Menyimpan ke Gold Layer
    # ===============================

    (
        df.writeTo(table("gold", "gold_program_studi"))
        .using("iceberg")
        .createOrReplace()
    )

    logger.info("Gold Program Studi berhasil dibuat.")

    return df
