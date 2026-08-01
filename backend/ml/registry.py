import os
import shutil
from datetime import datetime

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# =====================================================
# Folder Registry
# =====================================================

MODEL_DIR = "models"

CLASSIFIER_PATH = os.path.join(
    MODEL_DIR,
    "gaussian_nb"
)

METADATA_PATH = os.path.join(
    MODEL_DIR,
    "metadata.txt"
)


def save_model(evaluation_result):
    """
    Menyimpan model terbaik hasil training
    beserta metadata model.
    """

    logger.info("=" * 60)
    logger.info("MODEL REGISTRY")
    logger.info("=" * 60)

    model = evaluation_result["model"]

    # =====================================================
    # Hapus model lama
    # =====================================================

    if os.path.exists(CLASSIFIER_PATH):
        shutil.rmtree(CLASSIFIER_PATH)

    # =====================================================
    # Simpan Model
    # =====================================================

    logger.info("Menyimpan Gaussian Naive Bayes...")

    model.save(CLASSIFIER_PATH)

    logger.info("✓ Model berhasil disimpan.")

    # =====================================================
    # Simpan Metadata
    # =====================================================

    with open(METADATA_PATH, "w") as f:

        f.write("MODEL REGISTRY\n")
        f.write("=" * 40 + "\n")
        f.write(f"Tanggal     : {datetime.now()}\n")
        f.write("Algoritma   : Gaussian Naive Bayes\n")
        f.write(f"Accuracy    : {evaluation_result['accuracy']:.4f}\n")
        f.write(f"Precision   : {evaluation_result['precision']:.4f}\n")
        f.write(f"Recall      : {evaluation_result['recall']:.4f}\n")
        f.write(f"F1 Score    : {evaluation_result['f1_score']:.4f}\n")

    logger.info("✓ Metadata berhasil disimpan.")

    logger.info("=" * 60)
    logger.info("MODEL BERHASIL DISIMPAN")
    logger.info("=" * 60)

    logger.info(f"Model    : {CLASSIFIER_PATH}")
    logger.info(f"Metadata : {METADATA_PATH}")

    return {
        "model_path": CLASSIFIER_PATH,
        "metadata_path": METADATA_PATH
    }