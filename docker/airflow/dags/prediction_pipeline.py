from __future__ import annotations

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# Pipeline Prediksi Tingkat Kelulusan Mahasiswa (ITERA)
#
# Alur: Raw Excel -> Bronze -> Silver -> Gold
#         -> Feature Store -> ML (Naive Bayes) -> Prediction
#
# Mode Docker: DAG menjalankan pipeline in-process pada container
# Airflow (driver PySpark) yang tersambung ke Spark Master
# (`spark://spark-master:7077`, profile `spark-docker`). Source
# code proyek dimount ke /opt/airflow agar driver dapat mengimpor
# backend/. Lihat docker-compose.yml untuk volume mount.
# ============================================================

DEFAULT_ARGS = {
    "owner": "nita",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2026, 1, 1),
    "catchup": False,
}

with DAG(
    dag_id="prediction_pipeline",
    default_args=DEFAULT_ARGS,
    description="Integrasi Gold Layer ke Feature Store untuk model prediksi kelulusan",
    schedule="@daily",
    tags=["gold-layer", "feature-store", "ml"],
) as dag:

    def _notify(task_name: str) -> None:
        print(f"[{datetime.now().isoformat()}] Task selesai: {task_name}")

    def _run_spark_pipeline() -> None:
        if "/opt/airflow" not in sys.path:
            sys.path.insert(0, "/opt/airflow")

        from backend.services.pipeline_entry import resolve_pipeline_file
        from backend.services.pipeline_service import run_pipeline

        run_pipeline(resolve_pipeline_file("req_data_rut.xlsx"))

    t_start = PythonOperator(
        task_id="start",
        python_callable=_notify,
        op_kwargs={"task_name": "start"},
    )

    t_pipeline = PythonOperator(
        task_id="run_spark_pipeline",
        python_callable=_run_spark_pipeline,
    )

    t_publish = PythonOperator(
        task_id="publish_serving",
        python_callable=_notify,
        op_kwargs={"task_name": "publish_serving (gold -> trino/iceberg)"},
    )

    t_end = PythonOperator(
        task_id="end",
        python_callable=_notify,
        op_kwargs={"task_name": "end"},
    )

    t_start >> t_pipeline >> t_publish >> t_end
