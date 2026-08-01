from backend.utils.logger import get_logger

from backend.feature_store.training_dataset import (
    create_training_dataset,
)

from backend.feature_store.inference_dataset import (
    create_inference_dataset,
)

logger = get_logger(__name__)


def run_feature_store():

    logger.info("=" * 60)
    logger.info("MEMULAI FEATURE STORE")
    logger.info("=" * 60)

    # ==========================================
    # Training Dataset
    # ==========================================

    logger.info("Membuat Training Dataset...")

    create_training_dataset()

    # ==========================================
    # Inference Dataset
    # ==========================================

    logger.info("Membuat Inference Dataset...")

    create_inference_dataset()

    logger.info("=" * 60)
    logger.info("FEATURE STORE BERHASIL DIBUAT")
    logger.info("=" * 60)