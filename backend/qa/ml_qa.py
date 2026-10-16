"""
Jalur ML terisolasi untuk pipeline QA.

Modul ini menghubungkan Feature Store QA (namespace ``qa_feature_store``)
dengan fungsi ML PRODUKSI yang SUDAH ADA TANPA mengubah:

  * aturan fitur / kolom  -> ``backend.ml.data_preparation`` (MODEL_A/B_*, TARGET)
  * aturan label          -> berasal dari Gold/Feature Store (tidak diubah)
  * logika model          -> ``backend.ml.train.train_model`` (Hybrid Naive Bayes)
  * logika prediksi       -> ``backend.ml.inference.run_inference``

Seluruh direktori output (model/Excel) mengikuti resolver
``backend.config.namespaces`` sehingga artefak QA tidak menimpa produksi.

Prasyarat: environment ``PIPELINE_NS=qa`` (dan direktori output QA) sudah
diset oleh DAG ``qa_pipeline`` sebelum fungsi di modul ini dipanggil.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from backend.config.namespaces import ml_output_dir
from backend.feature_store import ml_export
from backend.ml import data_preparation as dp

# Kolom tambahan yang dibutuhkan output inference (selain fitur model).
_INFERENCE_EXTRA_COLUMNS = [
    "ipk_kategori",
    "selisih_sks",
    "jk_enc",
    "kecepatan_sks_per_semester",
]


def _feature_config(key):
    """Konfigurasi fitur yang SAMA dengan data_preparation.get_feature_config."""
    if key == "B":
        return dp.MODEL_B_CAT, dp.MODEL_B_NUM
    return dp.MODEL_A_CAT, dp.MODEL_A_NUM


def load_ml_frames():
    """Baca Feature Store QA -> kerangka ML (baca-saja, tanpa menulis tabel)."""
    training_fs, inference_fs = ml_export.load_feature_store_frames()
    ml_training = ml_export.build_ml_training_frame(training_fs)
    ml_inference = ml_export.build_ml_inference_frame(inference_fs)
    return ml_training, ml_inference


def get_training_data_qa(cat_cols, num_cols):
    """Split train/test (parameter SAMA dengan data_preparation) dari FS QA."""
    ml_training, _ = load_ml_frames()
    frame = ml_training.select(
        "id_mahasiswa", *(cat_cols + num_cols), "label"
    ).toPandas()

    X = frame[cat_cols + num_cols].copy()
    y = frame["label"].copy()

    return train_test_split(
        X,
        y,
        test_size=dp.TEST_SIZE,
        random_state=dp.RANDOM_STATE,
        stratify=y,
    )


def train_model_qa(model_name, key):
    """Latih model pada data Feature Store QA memakai train_model produksi.

    ``key`` in {"A", "B"} menentukan fitur (identik dengan jalur produksi).
    Model (.joblib) + metadata (.json) ditulis ke PIPELINE_MODEL_DIR
    (default: direktori model produksi; QA: models/qa).
    """
    from backend.ml.train import train_model

    cat_cols, num_cols = _feature_config(key)
    X_train, X_test, y_train, y_test = get_training_data_qa(cat_cols, num_cols)

    # Urutan argumen PERSIS seperti train.py::__main__.
    return train_model(
        X_train, y_train, X_test, y_test, cat_cols, num_cols, model_name
    )


def inference_data_loader_qa():
    """Loader data inference dari Feature Store QA.

    Mengembalikan (X, ids, df_inference) dengan kontrak SAMA seperti
    ``data_preparation.get_inference_data(model="A")``.
    """
    _, ml_inference = load_ml_frames()
    cat_cols, num_cols = _feature_config("A")

    extra = [c for c in _INFERENCE_EXTRA_COLUMNS if c not in cat_cols + num_cols]
    frame = ml_inference.select(
        "id_mahasiswa", *(cat_cols + num_cols), *extra
    ).toPandas()

    X = frame[cat_cols + num_cols].copy()
    ids = frame["id_mahasiswa"].values
    return X, ids, frame


def run_inference_qa():
    """Inference QA: model QA -> prediksi atas Feature Store QA -> Excel QA."""
    from backend.ml.inference import run_inference

    return run_inference(
        "model_a_utama",
        data_loader=inference_data_loader_qa,
        output_dir_path=ml_output_dir(),
        output_filename="inference_result_model_a_utama.xlsx",
    )
