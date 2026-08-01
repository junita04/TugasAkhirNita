from pathlib import Path

from backend.bronze.bronze import load_all_sheets_to_bronze
from backend.silver.silver import process_all_tables
from backend.gold.gold import process_gold
from backend.feature_store.feature_store import run_feature_store

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

    # Feature Store
    run_feature_store()

    logger.info("=" * 60)
    logger.info("PIPELINE BERHASIL")
    logger.info("=" * 60)