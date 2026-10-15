import json
import os
import shutil
from datetime import datetime

import joblib

from backend.config.settings import MODEL_DIR
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_NAME = "hybrid_naive_bayes"
MODEL_VERSION = "v1.0.0"

ARTIFACT_DIR = os.path.join(MODEL_DIR, "hybrid_naive_bayes")


def _paths():
    return {
        "dir": ARTIFACT_DIR,
        "model": os.path.join(ARTIFACT_DIR, "model.joblib"),
        "metadata": os.path.join(ARTIFACT_DIR, "metadata.json"),
    }


def save_model(training_result):
    """
    Menyimpan model final (HybridNaiveBayes) beserta metadata lengkap.
    """

    logger.info("=" * 60)
    logger.info(f"MODEL REGISTRY - SAVE ({MODEL_NAME}) v{MODEL_VERSION}")
    logger.info("=" * 60)

    pipeline_full = training_result["pipeline_full"]
    paths = _paths()

    if os.path.exists(paths["dir"]):
        shutil.rmtree(paths["dir"])

    os.makedirs(paths["dir"], exist_ok=True)

    joblib.dump(pipeline_full, paths["model"])
    logger.info(f"Model artifact tersimpan : {paths['model']}")

    metadata = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "model_type": "HybridNaiveBayes",
        "best_config": training_result["best_config"],
        "feature_names": training_result["feature_columns"],
        "categorical_features": training_result["categorical_features"],
        "numerical_features": training_result["numerical_features"],
        "target_name": training_result["target_column"],
        "identifier_column": training_result["identifier_column"],
        "training_row_count": training_result["n_records"],
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "holdout": training_result["holdout"],
        "artifact_path": paths["model"],
    }

    with open(paths["metadata"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"Metadata tersimpan       : {paths['metadata']}")
    logger.info("=" * 60)
    logger.info("MODEL BERHASIL DISIMPAN")
    logger.info("=" * 60)

    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "artifact_path": paths["model"],
        "metadata_path": paths["metadata"],
    }


def load_model():
    """
    Memuat model artifact dari Model Registry.
    """
    paths = _paths()

    if not os.path.exists(paths["model"]):
        raise FileNotFoundError(
            f"Model artifact tidak ditemukan: {paths['model']}"
        )

    pipeline = joblib.load(paths["model"])

    with open(paths["metadata"], "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return pipeline, metadata
