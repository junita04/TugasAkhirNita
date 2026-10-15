from __future__ import annotations

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# Pipeline TRAINING (Tahap 4) - Hybrid Naive Bayes
#
# Mengikuti jalur training TERBARU yang sudah ditetapkan pada
# `backend/ml/train.py` (blok __main__):
#   * Model A (utama)      : total_sks, jumlah_mk
#   * Model B (pembanding) : selisih_sks, kecepatan_sks_per_semester
#
# Setiap model menjadi task Airflow terpisah agar durasi NATIVE
# terekam di metadata Airflow. Task memakai ULANG fungsi yang sama
# (data_preparation + train_model) TANPA mengubah fitur, bobot,
# algoritma Hybrid Naive Bayes, Stratified 10-Fold CV, kriteria
# evaluasi, threshold, maupun metode prediksi.
#
# MANUAL TRIGGER ONLY (schedule=None). Jalankan ETL terlebih dahulu
# (DAG prediction_pipeline).
# ============================================================

TRAIN_SPECS = {
    "model_a_utama": "A",
    "model_b_pembanding": "B",
}

DEFAULT_ARGS = {
    "owner": "nita",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2026, 1, 1),
    "catchup": False,
}


def _boot():
    if "/opt/airflow" not in sys.path:
        sys.path.insert(0, "/opt/airflow")
    # train.py memakai bare import `from hybrid_nb import HybridNaiveBayes`,
    # sehingga backend/ml harus ada di sys.path (pola sama seperti inference.py).
    if "/opt/airflow/backend/ml" not in sys.path:
        sys.path.insert(0, "/opt/airflow/backend/ml")


def _train(model_name: str):
    _boot()
    from backend.ml.data_preparation import (
        get_model_a_data,
        get_model_b_data,
        get_feature_config,
    )
    from backend.ml.train import train_model

    key = TRAIN_SPECS[model_name]
    if key == "A":
        X_train, X_test, y_train, y_test = get_model_a_data()
    else:
        X_train, X_test, y_train, y_test = get_model_b_data()

    features = get_feature_config(key)

    # Urutan argumen PERSIS seperti train.py::__main__. Jika gagal,
    # exception dibiarkan naik sehingga task Airflow berstatus FAIL.
    model, metadata = train_model(
        X_train, y_train, X_test, y_test,
        features["categorical"], features["numerical"], model_name,
    )
    print(
        f"[tahap4] TRAIN OK: {model_name} "
        f"(accuracy={metadata['holdout_metrics']['accuracy']:.4f})"
    )


with DAG(
    dag_id="training_pipeline",
    default_args=DEFAULT_ARGS,
    description="Training Tahap 4: Model A (utama) + Model B (pembanding) - Hybrid Naive Bayes",
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["tahap-4", "training", "ml", "model-a", "model-b"],
) as dag:

    t_model_a = PythonOperator(
        task_id="train_model_a_utama",
        python_callable=_train,
        op_kwargs={"model_name": "model_a_utama"},
    )

    t_model_b = PythonOperator(
        task_id="train_model_b_pembanding",
        python_callable=_train,
        op_kwargs={"model_name": "model_b_pembanding"},
    )

    t_model_a >> t_model_b
