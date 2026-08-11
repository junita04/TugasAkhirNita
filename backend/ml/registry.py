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

FEATURE_PIPELINE_PATH = os.path.join(
    MODEL_DIR,
    "feature_pipeline"
)

METADATA_PATH = os.path.join(
    MODEL_DIR,
    "metadata.txt"
)


def save_model(evaluation_result):
    """
    Menyimpan model terbaik hasil training beserta metadata model.

    Selain model Naive Bayes, disimpan juga pipeline fitur yang sudah
    di-fit pada data training (StringIndexer jenis kelamin + VectorAssembler)
    agar pemetaan indeks fitur pada saat inferensi identik dengan training.
    """

    logger.info("=" * 60)
    logger.info("MODEL REGISTRY")
    logger.info("=" * 60)

    model = evaluation_result["model"]
    feature_pipeline_model = evaluation_result["feature_pipeline_model"]
    label_order = list(evaluation_result.get("label_order", []))

    # =====================================================
    # Hapus model lama
    # =====================================================

    for path in (CLASSIFIER_PATH, FEATURE_PIPELINE_PATH):
        if os.path.exists(path):
            shutil.rmtree(path)

    # =====================================================
    # Simpan Model
    # =====================================================

    logger.info("Menyimpan Gaussian Naive Bayes...")

    model.save(CLASSIFIER_PATH)

    logger.info("✓ Model berhasil disimpan.")

    # =====================================================
    # Simpan Feature Pipeline
    # =====================================================

    logger.info("Menyimpan Feature Pipeline...")

    feature_pipeline_model.save(FEATURE_PIPELINE_PATH)

    logger.info("✓ Feature Pipeline berhasil disimpan.")

    # =====================================================
    # Simpan Metadata
    # =====================================================

    with open(METADATA_PATH, "w", encoding="utf-8") as f:

        f.write("MODEL REGISTRY\n")
        f.write("=" * 40 + "\n")
        f.write(f"Tanggal     : {datetime.now()}\n")
        f.write("Algoritma   : Gaussian Naive Bayes\n")
        f.write(f"Accuracy    : {evaluation_result['accuracy']:.4f}\n")
        f.write(f"Precision   : {evaluation_result['precision']:.4f}\n")
        f.write(f"Recall      : {evaluation_result['recall']:.4f}\n")
        f.write(f"F1 Score    : {evaluation_result['f1_score']:.4f}\n")
        f.write(f"Label Order : {label_order}\n")

    logger.info("✓ Metadata berhasil disimpan.")

    logger.info("=" * 60)
    logger.info("MODEL BERHASIL DISIMPAN")
    logger.info("=" * 60)

    logger.info(f"Model           : {CLASSIFIER_PATH}")
    logger.info(f"Feature Pipeline: {FEATURE_PIPELINE_PATH}")
    logger.info(f"Metadata        : {METADATA_PATH}")

    return {
        "model_path": CLASSIFIER_PATH,
        "feature_pipeline_path": FEATURE_PIPELINE_PATH,
        "metadata_path": METADATA_PATH,
        "label_order": label_order,
    }