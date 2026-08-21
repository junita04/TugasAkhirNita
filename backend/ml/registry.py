import json
import os
import shutil
from datetime import datetime

import joblib

from backend.config.settings import MODEL_DIR
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_NAME = "gaussian_nb_lulusan"

# =====================================================
# Revisi Tahap 3 (v3.0.0): dataset baru
# `(asli)req_data_rut (1).xlsx` (dataset revisi final).
# Versi sebelumnya (v1.0.0, v2.0.0) TIDAK ditimpa.
# Artifact revisi dataset baru disimpan di direktori baru.
# =====================================================
MODEL_VERSION = "v3.0.0"

ARTIFACT_DIR = os.path.join(MODEL_DIR, "gaussian_nb_v3")


def _variant_dir(use_smote):
    """Subdirektori artifact per varian (revisi Tahap 3, dataset baru)."""
    sub = "with_smote" if use_smote else "without_smote"
    return os.path.join(ARTIFACT_DIR, sub)


def _paths(use_smote):
    directory = _variant_dir(use_smote)
    return {
        "dir": directory,
        "model": os.path.join(directory, "model.joblib"),
        "metadata": os.path.join(directory, "metadata.json"),
    }


def save_model(training_result):
    """
    Menyimpan model final (GaussianNB, TANPA StandardScaler) beserta
    metadata lengkap ke Model Registry.

    MODEL A (without_smote): GaussianNB()
    MODEL B (with_smote)   : SMOTE + GaussianNB (imblearn pipeline)

    Metadata mencatat:
      - variant (without_smote / with_smote)
      - preprocessing (kosong, tanpa scaler)
      - feature names, class mapping, cv summary, holdout metrics.
    """

    use_smote = training_result.get("use_smote", False)
    variant = "with_smote" if use_smote else "without_smote"

    logger.info("=" * 60)
    logger.info(f"MODEL REGISTRY - SAVE ({variant.upper()}) v{MODEL_VERSION}")
    logger.info("=" * 60)

    pipeline_full = training_result["pipeline_full"]

    paths = _paths(use_smote)

    if os.path.exists(paths["dir"]):
        shutil.rmtree(paths["dir"])

    os.makedirs(paths["dir"], exist_ok=True)

    # =====================================================
    # Simpan artifact
    # =====================================================

    joblib.dump(pipeline_full, paths["model"])

    logger.info(f"✓ Model artifact tersimpan : {paths['model']}")

    # =====================================================
    # Metadata
    # =====================================================

    metadata = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "variant": variant,
        "use_smote": use_smote,
        "sampling": {"method": "SMOTE" if use_smote else None},
        "model_type": "GaussianNB",
        "preprocessing": [],  # revisi Tahap 3: TANPA scaler
        "has_scaler": False,
        "feature_names": training_result["feature_columns"],
        "target_name": training_result["target_column"],
        "identifier_column": training_result["identifier_column"],
        "positive_class": training_result["positive_class"],
        "class_mapping": training_result["class_mapping"],
        "class_distribution": training_result["class_distribution"],
        "training_row_count": training_result["n_records"],
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cv": training_result["cv"],
        "cv_summary": training_result["cv_summary"],
        "holdout": training_result["holdout"],
        "test_size": training_result["test_size"],
        "random_state": training_result["random_state"],
        "artifact_path": paths["model"],
    }

    with open(paths["metadata"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Metadata tersimpan       : {paths['metadata']}")

    logger.info("=" * 60)
    logger.info("MODEL BERHASIL DISIMPAN")
    logger.info("=" * 60)

    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "variant": variant,
        "artifact_path": paths["model"],
        "metadata_path": paths["metadata"],
    }


def load_model(use_smote=False):
    """
    Memuat model artifact (revisi v3.0.0, dataset baru) dari Model Registry.
    """

    paths = _paths(use_smote)

    if not os.path.exists(paths["model"]):
        raise FileNotFoundError(
            f"Model artifact tidak ditemukan: {paths['model']}"
        )

    pipeline = joblib.load(paths["model"])

    with open(paths["metadata"], "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return pipeline, metadata