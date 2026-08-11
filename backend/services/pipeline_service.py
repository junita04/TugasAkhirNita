from pathlib import Path

from backend.bronze.bronze import load_all_sheets_to_bronze
from backend.silver.silver import process_all_tables
from backend.gold.gold import process_gold
from backend.feature_store.feature_store import run_feature_store
from backend.config.settings import POSTGRES_ENABLED
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline(file_path: Path):
    """
    Menjalankan seluruh pipeline ETL:
    Bronze -> Silver -> Gold -> Feature Store
    """

    logger.info("=" * 60)
    logger.info("MENJALANKAN DATA PIPELINE")
    logger.info("=" * 60)

    # Bronze
    load_all_sheets_to_bronze(file_path)

    # Silver
    process_all_tables()

    # Gold
    process_gold()

    # PostgreSQL serving layer (opsional; untuk Superset lewat DB langsung).
    # Iceberg + Trino adalah sumber utama Superset, sehingga publish ke
    # PostgreSQL dapat dimatikan pada mode lokal tanpa Postgres.
    if POSTGRES_ENABLED:
        from backend.serving.postgres_sink import publish_gold_tables
        from backend.spark.session import get_spark

        logger.info("PostgreSQL serving aktif: publish tabel Gold...")
        publish_gold_tables(get_spark("Gold PostgreSQL Publish"))
    else:
        logger.info("POSTGRES_ENABLED=false -> publish ke PostgreSQL dilewati.")

    # Feature Store
    run_feature_store()

    # =====================================================
    # Tutup SparkSession sekali di akhir pipeline
    # =====================================================

    from backend.spark.session import get_spark

    spark = get_spark("Pipeline")
    spark.stop()

    logger.info("=" * 60)
    logger.info("PIPELINE BERHASIL")
    logger.info("=" * 60)
