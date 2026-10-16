from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# QA PIPELINE - jalur TERISOLASI dari pipeline produksi.
#
# Tujuan: memproses dataset baru `(asli)req_data_rut (baruu).xlsx`
# dari awal (Bronze) sampai prediksi (Iceberg) TANPA menyentuh satu pun
# target produksi.
#
# Isolasi dilakukan lewat env `PIPELINE_NS=qa` + direktori output QA:
#   * namespace Iceberg   : qa_bronze / qa_silver / qa_gold / qa_feature_store
#   * tabel final         : iceberg.qa_gold.inference_result_model_a_utama
#   * model + metadata    : /opt/airflow/models/qa
#   * Excel hasil         : /opt/airflow/data/qa
#   * laporan JSON        : /opt/airflow/logs/qa
#
# DAG ini DEFAULT PAUSED (is_paused_upon_creation=True) dan
# schedule=None (MANUAL TRIGGER ONLY). DAG produksi tidak diubah.
#
# WAJIB: sebelum menjalankan, jalankan `scripts/qa_prod_signature.py`
# (read-only) untuk merekam signature produksi, lalu bandingkan sesudahnya.
# ============================================================

DEFAULT_ARGS = {
    "owner": "nita",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2026, 1, 1),
    "catchup": False,
}

FILE_NAME = "(asli)req_data_rut (baruu).xlsx"

QA_NAMESPACE = "qa"
QA_MODEL_DIR = "/opt/airflow/models/qa"
QA_ML_OUTPUT_DIR = "/opt/airflow/data/qa"
QA_DATA_OUTPUT_DIR = "/opt/airflow/data/qa"
QA_LOG_DIR = "/opt/airflow/logs/qa"


def _boot():
    if "/opt/airflow" not in sys.path:
        sys.path.insert(0, "/opt/airflow")
    # train.py memakai bare import `from hybrid_nb import HybridNaiveBayes`.
    if "/opt/airflow/backend/ml" not in sys.path:
        sys.path.insert(0, "/opt/airflow/backend/ml")


def _qa_env():
    """Aktifkan isolasi QA. Nilai di-set eksplisit agar tidak ambigu."""
    os.environ["PIPELINE_NS"] = QA_NAMESPACE

    for name in (QA_MODEL_DIR, QA_ML_OUTPUT_DIR, QA_DATA_OUTPUT_DIR, QA_LOG_DIR):
        os.makedirs(name, exist_ok=True)

    os.environ["PIPELINE_MODEL_DIR"] = QA_MODEL_DIR
    os.environ["PIPELINE_ML_OUTPUT_DIR"] = QA_ML_OUTPUT_DIR
    os.environ["PIPELINE_DATA_OUTPUT_DIR"] = QA_DATA_OUTPUT_DIR
    os.environ["PIPELINE_LOG_DIR"] = QA_LOG_DIR

    # Postgres serving harus tetap nonaktif pada jalur QA.
    os.environ["POSTGRES_ENABLED"] = "false"


def _resolve_file():
    from backend.services.pipeline_entry import resolve_pipeline_file

    return resolve_pipeline_file(FILE_NAME)


def _stage_bronze_qa():
    _boot()
    _qa_env()
    from backend.bronze.bronze import load_all_sheets_to_bronze

    success, skipped = load_all_sheets_to_bronze(_resolve_file())
    print(f"[qa] BRONZE OK: tables={success} skipped={skipped}")


def _stage_silver_qa():
    _boot()
    _qa_env()
    from backend.silver.silver import process_all_tables

    process_all_tables()
    print("[qa] SILVER OK")


def _stage_gold_qa():
    _boot()
    _qa_env()
    from backend.gold.gold import process_gold

    process_gold()
    print("[qa] GOLD OK")


def _stage_feature_store_qa():
    _boot()
    _qa_env()
    from backend.feature_store.feature_store import run_feature_store

    run_feature_store()
    print("[qa] FEATURE_STORE OK")


def _stage_prepare_ml_qa():
    _boot()
    _qa_env()
    from backend.feature_store.ml_export import validate_feature_store_datasets

    report = validate_feature_store_datasets()
    print(
        "[qa] ML DATASET READY: "
        f"training_rows={report['training']['rows']} "
        f"inference_rows={report['inference']['rows']} "
        f"missing={report['training']['missing_columns'] + report['inference']['missing_columns']}"
    )


def _stage_train_qa(model_name: str, key: str):
    _boot()
    _qa_env()
    from backend.qa.ml_qa import train_model_qa

    _model, metadata = train_model_qa(model_name, key)
    print(
        f"[qa] TRAIN OK: {model_name} "
        f"(accuracy={metadata['holdout_metrics']['accuracy']:.4f})"
    )


def _stage_inference_qa():
    _boot()
    _qa_env()
    from backend.qa.ml_qa import run_inference_qa

    df = run_inference_qa()
    print(f"[qa] INFERENCE OK: {len(df)} rows")


def _stage_iceberg_output_qa():
    _boot()
    _qa_env()
    from backend.ml.iceberg_output import run_iceberg_output

    report = run_iceberg_output()
    if report.get("status") != "SUCCESS":
        raise RuntimeError(f"[qa] Iceberg output FAILED: {report.get('status')}")
    print(f"[qa] ICEBERG_OUTPUT OK: {report['status']}")


def _stage_validate_qa():
    _boot()
    _qa_env()
    from backend.spark.session import get_spark
    from backend.config.namespaces import table

    spark = get_spark("QA - Validate")

    targets = [
        ("bronze", "data_referensi_mahasiswa"),
        ("silver", "silver_mahasiswa"),
        ("gold", "dim_mahasiswa"),
        ("feature_store", "training_dataset"),
        ("feature_store", "inference_dataset"),
        ("gold", "inference_result_model_a_utama"),
    ]

    print("[qa] VALIDATION (read-only)")
    failures = []
    for schema, name in targets:
        full = table(schema, name)
        try:
            count = spark.table(full).count()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{full}: ERROR {exc}")
            print(f"    {full:<60} : ERROR")
            continue
        print(f"    {full:<60} : {count} rows")
        if count == 0:
            failures.append(f"{full}: EMPTY")

    if failures:
        raise RuntimeError(f"[qa] Validasi gagal: {failures}")
    print("[qa] VALIDATION OK")


def _notify(task_name: str) -> None:
    print(f"[{datetime.now().isoformat()}] [qa] Task selesai: {task_name}")


with DAG(
    dag_id="qa_full_pipeline",
    default_args=DEFAULT_ARGS,
    description="QA (terisolasi): dataset baru -> Bronze/Silver/Gold/FeatureStore QA -> train -> inference -> Iceberg QA",
    schedule=None,
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["qa", "isolated", "etl", "training", "inference"],
) as dag:

    t_start = PythonOperator(
        task_id="start",
        python_callable=_notify,
        op_kwargs={"task_name": "start"},
    )

    t_bronze = PythonOperator(task_id="bronze_qa", python_callable=_stage_bronze_qa)
    t_silver = PythonOperator(task_id="silver_qa", python_callable=_stage_silver_qa)
    t_gold = PythonOperator(task_id="gold_qa", python_callable=_stage_gold_qa)
    t_feature_store = PythonOperator(
        task_id="feature_store_qa", python_callable=_stage_feature_store_qa
    )
    t_prepare_ml = PythonOperator(
        task_id="prepare_ml_qa", python_callable=_stage_prepare_ml_qa
    )
    t_train_a = PythonOperator(
        task_id="train_a_qa",
        python_callable=_stage_train_qa,
        op_kwargs={"model_name": "model_a_utama", "key": "A"},
    )
    t_train_b = PythonOperator(
        task_id="train_b_qa",
        python_callable=_stage_train_qa,
        op_kwargs={"model_name": "model_b_pembanding", "key": "B"},
    )
    t_inference = PythonOperator(
        task_id="inference_qa", python_callable=_stage_inference_qa
    )
    t_iceberg = PythonOperator(
        task_id="iceberg_output_qa", python_callable=_stage_iceberg_output_qa
    )
    t_validate = PythonOperator(
        task_id="validate_qa", python_callable=_stage_validate_qa
    )
    t_end = PythonOperator(
        task_id="end",
        python_callable=_notify,
        op_kwargs={"task_name": "end"},
    )

    (
        t_start
        >> t_bronze
        >> t_silver
        >> t_gold
        >> t_feature_store
        >> t_prepare_ml
        >> t_train_a
        >> t_train_b
        >> t_inference
        >> t_iceberg
        >> t_validate
        >> t_end
    )
