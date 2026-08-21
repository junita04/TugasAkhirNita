from __future__ import annotations

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# Pipeline INFERENCE (Tahap 4) - Prediksi + Iceberg Output
#
# Membaca inference dataset dari Feature Store (iceberg.feature_store
# .inference_dataset, hasil ETL), memuat model v3.0.0 dari registry,
# lalu:
#   * inference       : prediksi 2 varian -> Parquet biasa di
#                       data/predictions/prediction_result_*.parquet
#   * iceberg_output  : Parquet -> tabel Iceberg feature_store
#                       .prediction_result_* (downstream Trino/Superset)
#
# Tiap tahap menjadi task Airflow terpisah agar durasi NATIVE terekam.
#
# MANUAL TRIGGER ONLY (schedule=None). Menjalankan ETL lalu training
# terlebih dahulu (DAG prediction_pipeline -> training_pipeline).
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


def _stage_inference():
    _boot()
    from backend.ml.inference import run_inference

    report = run_inference()
    if report.get("status") != "SUCCESS":
        raise RuntimeError(f"Inference FAILED: {report.get('status')}")
    print(f"[tahap4] INFERENCE OK: {report['schema_validation']}")


def _stage_iceberg_output():
    _boot()
    from backend.ml.iceberg_output import run_iceberg_output

    report = run_iceberg_output()
    if report.get("status") != "SUCCESS":
        raise RuntimeError(f"Iceberg output FAILED: {report.get('status')}")
    print(f"[tahap4] ICEBERG_OUTPUT OK: {report['status']}")


with DAG(
    dag_id="inference_pipeline",
    default_args=DEFAULT_ARGS,
    description="Inference Tahap 4: prediksi Parquet + output Iceberg (prediction_result)",
    schedule=None,
    catchup=False,
    tags=["tahap-4", "inference", "prediction", "ml"],
) as dag:

    t_inference = PythonOperator(
        task_id="inference",
        python_callable=_stage_inference,
    )

    t_iceberg = PythonOperator(
        task_id="iceberg_output",
        python_callable=_stage_iceberg_output,
    )

    t_inference >> t_iceberg