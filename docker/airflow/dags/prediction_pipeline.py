from __future__ import annotations

from datetime import datetime, timedelta
from json import loads
from urllib.request import Request, urlopen

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# Pipeline Prediksi Tingkat Kelulusan Mahasiswa (ITERA)
#
# Alur: Raw Excel -> Bronze -> Silver -> Gold
#         -> Feature Store -> ML (Naive Bayes) -> Serving
#
# Catatan:
#   - Mode 'cluster': jalankan Spark via spark-master (docker).
#   - Mode 'local'  : pipeline tetap berjalan di mesin lokal,
#     DAG ini menjadi kerangka orkestrasi otomatis.
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

    t_start = PythonOperator(
        task_id="start",
        python_callable=_notify,
        op_kwargs={"task_name": "start"},
    )

    def _trigger_host_pipeline() -> None:
        request = Request(
            "http://host.docker.internal:8000/pipeline/run",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            payload = loads(response.read().decode("utf-8"))
            if response.status != 200 or payload.get("status") != "success":
                raise RuntimeError(f"Host pipeline failed: {payload}")

    t_pipeline = PythonOperator(
        task_id="run_local_spark_pipeline",
        python_callable=_trigger_host_pipeline,
    )

    t_publish = PythonOperator(
        task_id="publish_serving",
        python_callable=_notify,
        op_kwargs={"task_name": "publish_serving (gold -> postgres/trino)"},
    )

    t_end = PythonOperator(
        task_id="end",
        python_callable=_notify,
        op_kwargs={"task_name": "end"},
    )

    t_start >> t_pipeline >> t_publish >> t_end
