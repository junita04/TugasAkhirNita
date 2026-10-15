from __future__ import annotations

import json
import socket
import urllib.request
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

# ============================================================
# DAG SMOKE TEST — READ-ONLY (TAHAP 7E)
#
# TIDAK menulis apa pun: tidak menjalankan pipeline ETL,
# tidak mengubah Bronze/Silver/Gold/Feature Store, tidak
# melatih model, tidak menjalankan inference.
#
# Tugas hanya memvalidasi konektivitas & keterbacaan:
#   1. PostgreSQL metadata Airflow (postgres-airflow)
#   2. MinIO  (health S3)
#   3. Trino  (health) -> HMS -> MinIO (Iceberg) via SELECT COUNT
#   4. Hive Metastore (TCP thrift)
#   5. Spark Master (hostname resolve + TCP 7077, informasional)
# ============================================================

POSTGRES_HOST = "postgres-airflow"
POSTGRES_PORT = 5432
POSTGRES_DB = "airflow"
POSTGRES_USER = "airflow"
POSTGRES_PASSWORD = "airflow-password"

MINIO_URL = "http://minio:9000"
TRINO_URL = "http://trino:8082"
HMS_HOST = "hive-metastore"
HMS_PORT = 9083
SPARK_HOST = "spark-master"
SPARK_PORT = 7077


def _http_status(url: str, timeout: int = 15) -> int:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status


def _tcp_reachable(host: str, port: int, timeout: int = 5) -> bool:
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.close()
    return True


def _check_postgres() -> str:
    import psycopg2

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        connect_timeout=5,
    )
    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
    conn.close()
    print(f"[smoke] PostgreSQL OK: {version.split(' on ')[0]}")
    return f"PostgreSQL OK ({POSTGRES_HOST}:{POSTGRES_PORT})"


def _check_minio() -> str:
    status = _http_status(f"{MINIO_URL}/minio/health/live")
    print(f"[smoke] MinIO OK: /minio/health/live HTTP {status}")
    return f"MinIO OK (HTTP {status})"


def _check_hms() -> str:
    _tcp_reachable(HMS_HOST, HMS_PORT)
    print(f"[smoke] Hive Metastore OK: {HMS_HOST}:{HMS_PORT} reachable")
    return f"HMS OK ({HMS_HOST}:{HMS_PORT})"


def _check_trino() -> str:
    status = _http_status(f"{TRINO_URL}/v1/info")
    print(f"[smoke] Trino OK: /v1/info HTTP {status}")
    return f"Trino OK (HTTP {status})"


def _check_trino_read() -> str:
    query = "SELECT COUNT(*) AS n FROM iceberg.gold.gold_mahasiswa"
    req = urllib.request.Request(
        f"{TRINO_URL}/v1/statement",
        data=query.encode("utf-8"),
        headers={"Content-Type": "text/plain", "X-Trino-User": "trino"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    rows = payload.get("data")
    next_uri = payload.get("nextUri")
    while rows is None and next_uri:
        with urllib.request.urlopen(next_uri, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        rows = payload.get("data")
        next_uri = payload.get("nextUri")

    count = rows[0][0]
    print(f"[smoke] Trino read OK: gold_mahasiswa COUNT = {count}")
    return f"Trino->Iceberg OK (gold_mahasiswa={count})"


def _check_spark_config() -> str:
    import os

    env = {k: os.environ.get(k) for k in ("SPARK_MODE", "SPARK_MASTER_URL", "ICEBERG_CATALOG", "ICEBERG_WAREHOUSE", "HIVE_METASTORE_URI", "S3_ENDPOINT")}
    try:
        _tcp_reachable(SPARK_HOST, SPARK_PORT)
        spark_tcp = "reachable"
    except Exception as exc:  # noqa: BLE001
        spark_tcp = f"unreachable ({exc.__class__.__name__})"
    print(f"[smoke] Spark env={env} tcp({SPARK_HOST}:{SPARK_PORT})={spark_tcp}")
    return f"Spark config ok (tcp={spark_tcp})"


with DAG(
    dag_id="pipeline_smoke_test",
    default_args={"owner": "nita", "retries": 1},
    description="Smoke test read-only: konektivitas Airflow->PG/MinIO/Trino/HMS + baca Iceberg (Tanpa tulis apa pun)",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["smoke-test", "read-only", "tahap-7e"],
) as dag:

    t_pg = PythonOperator(task_id="check_postgres", python_callable=_check_postgres)
    t_minio = PythonOperator(task_id="check_minio", python_callable=_check_minio)
    t_hms = PythonOperator(task_id="check_hms", python_callable=_check_hms)
    t_trino = PythonOperator(task_id="check_trino", python_callable=_check_trino)
    t_trino_read = PythonOperator(task_id="check_trino_read_iceberg", python_callable=_check_trino_read)
    t_spark = PythonOperator(task_id="check_spark_config", python_callable=_check_spark_config)

    [t_pg, t_minio, t_hms, t_trino, t_spark] >> t_trino_read
