from __future__ import annotations

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# Pipeline TRAINING (Tahap 4) - GaussianNB dua varian
#
# Membaca training dataset dari Feature Store (iceberg.feature_store
# .training_dataset, hasil ETL) lalu melatih & menyimpan model ke Model
# Registry v3.0.0:
#   * without_smote : GaussianNB() baseline
#   * with_smote    : SMOTE + GaussianNB (imblearn pipeline)
#
# Tiap varian menjadi task Airflow terpisah agar durasi NATIVE training
# tiap varian terekam di metadata Airflow.
#
# MANUAL TRIGGER ONLY (schedule=None). Menjalankan ETL terlebih dahulu
# (DAG prediction_pipeline).
# ============================================================

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


def _train_without_smote():
    _boot()
    from backend.ml.evaluate import _run_variant

    result = _run_variant(use_smote=False)
    if result["status"] != "SUCCESS":
        raise RuntimeError(f"Training without_smote FAILED: {result['status']}")
    print(f"[tahap4] TRAIN without_smote OK: {result['registry_info']}")


def _train_with_smote():
    _boot()
    from backend.ml.evaluate import _run_variant

    result = _run_variant(use_smote=True)
    if result["status"] != "SUCCESS":
        raise RuntimeError(f"Training with_smote FAILED: {result['status']}")
    print(f"[tahap4] TRAIN with_smote OK: {result['registry_info']}")


with DAG(
    dag_id="training_pipeline",
    default_args=DEFAULT_ARGS,
    description="Training Tahap 4: GaussianNB without_smote + with_smote (registry v3.0.0)",
    schedule=None,
    catchup=False,
    tags=["tahap-4", "training", "ml"],
) as dag:

    t_without = PythonOperator(
        task_id="train_without_smote",
        python_callable=_train_without_smote,
    )

    t_with = PythonOperator(
        task_id="train_with_smote",
        python_callable=_train_with_smote,
    )

    [t_without, t_with]