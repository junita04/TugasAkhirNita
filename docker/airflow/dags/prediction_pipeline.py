from __future__ import annotations

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# Pipeline ETL (Tahap 4) - Bronze -> Silver -> Gold -> Feature Store
#
# Menggunakan dataset baru `(asli)req_data_rut (1).xlsx` (Tahap 1-3 PASS).
# Tiap tahap dipisahkan menjadi task Airflow tersendiri agar durasi NATIVE
# tiap tahap (bronze/silver/gold/feature_store) terekam di metadata Airflow.
#
# Mode Docker: task berjalan in-process pada container Airflow (driver
# PySpark) yang tersambung ke Spark Master (`spark://spark-master:7077`,
# profile `spark-docker`). Source code proyek dimount ke /opt/airflow
# agar driver dapat mengimpor backend/. Lihat docker-compose.yml.
#
# MANUAL TRIGGER ONLY (schedule=None). Tidak dijadwalkan otomatis.
# ============================================================

DEFAULT_ARGS = {
    "owner": "nita",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2026, 1, 1),
    "catchup": False,
}

FILE_NAME = "(asli)req_data_rut (1).xlsx"


def _boot():
    if "/opt/airflow" not in sys.path:
        sys.path.insert(0, "/opt/airflow")


def _resolve_file():
    from backend.services.pipeline_entry import resolve_pipeline_file

    return resolve_pipeline_file(FILE_NAME)


def _stage_bronze():
    _boot()
    from backend.bronze.bronze import load_all_sheets_to_bronze

    success, skipped = load_all_sheets_to_bronze(_resolve_file())
    print(f"[tahap4] BRONZE OK: tables={success} skipped={skipped}")


def _stage_silver():
    _boot()
    from backend.silver.silver import process_all_tables

    process_all_tables()
    print("[tahap4] SILVER OK")


def _stage_gold():
    _boot()
    from backend.gold.gold import process_gold

    process_gold()
    print("[tahap4] GOLD OK")


def _stage_feature_store():
    _boot()
    from backend.feature_store.feature_store import run_feature_store

    run_feature_store()
    print("[tahap4] FEATURE_STORE OK")


def _notify(task_name: str) -> None:
    print(f"[{datetime.now().isoformat()}] Task selesai: {task_name}")


with DAG(
    dag_id="prediction_pipeline",
    default_args=DEFAULT_ARGS,
    description="ETL Tahap 4: Bronze -> Silver -> Gold -> Feature Store (dataset baru)",
    schedule=None,
    catchup=False,
    tags=["tahap-4", "etl", "gold-layer", "feature-store"],
) as dag:

    t_start = PythonOperator(
        task_id="start",
        python_callable=_notify,
        op_kwargs={"task_name": "start"},
    )

    t_bronze = PythonOperator(
        task_id="bronze",
        python_callable=_stage_bronze,
    )

    t_silver = PythonOperator(
        task_id="silver",
        python_callable=_stage_silver,
    )

    t_gold = PythonOperator(
        task_id="gold",
        python_callable=_stage_gold,
    )

    t_feature_store = PythonOperator(
        task_id="feature_store",
        python_callable=_stage_feature_store,
    )

    t_end = PythonOperator(
        task_id="end",
        python_callable=_notify,
        op_kwargs={"task_name": "end"},
    )

    t_start >> t_bronze >> t_silver >> t_gold >> t_feature_store >> t_end