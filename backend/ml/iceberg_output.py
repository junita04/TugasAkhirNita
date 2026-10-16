"""
Tahap 6 — Iceberg Output (Excel -> Iceberg) untuk Model Utama (Model A).

Membaca hasil inference Model Utama yang SUDAH tersimpan sebagai Excel:
  * data/data fix/inference_result_model_a_utama.xlsx

lalu menyimpannya sebagai tabel Apache Iceberg FINAL untuk downstream
(Trino/Superset):

  * iceberg.gold.inference_result_model_a_utama

TIDAK melakukan training ulang, TIDAK mengubah hasil prediksi, TIDAK
menambahkan StandardScaler/SMOTE, dan TIDAK menyentuh pipeline Tahap 1-5.

Catatan teknis (Trino v467 REST API):
  Endpoint POST /v1/statement menerima SQL sebagai plain-text body.
  Pengiriman JSON {"query": "..."} memicu SYNTAX_ERROR "mismatched input '{'"
  karena Trino memperlakukan seluruh body sebagai teks SQL.
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd
import requests

from backend.config.namespaces import ml_output_dir, log_dir, table, namespace_prefix
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# Source file dari inference pipeline. Dievaluasi saat dipanggil agar
# mengikuti PIPELINE_ML_OUTPUT_DIR (produksi/QA).
def excel_source():
    return ml_output_dir() / "inference_result_model_a_utama.xlsx"


TRINO_URL = "http://trino:8082/v1/statement"
TRINO_USER = "airflow"
TRINO_TIMEOUT = 120


def _trino_headers():
    return {
        "X-Trino-User": TRINO_USER,
        "X-Trino-Catalog": "iceberg",
        "X-Trino-Schema": f"{namespace_prefix()}gold",
    }


# Tabel target FINAL. Dievaluasi saat dipanggil agar mengikuti PIPELINE_NS.
def target_table():
    return table("gold", "inference_result_model_a_utama", catalog="iceberg")


IDENTIFIER_COLUMN = "id_mahasiswa"

REQUIRED_COLUMNS = [
    IDENTIFIER_COLUMN,
    "IPK_kategori", "selisih_sks", "jk_enc",
    "kecepatan_sks_per_semester",
    "prob_tepat_waktu", "prob_terlambat",
    "prediksi",
]

EXPECTED_DISTRIBUTION = {"0": 1476, "1": 10862}  # referensi (bisa berubah tiap run)

BATCH_SIZE = 500


class IcebergOutputError(RuntimeError):
    """Error spesifik proses penyimpanan hasil inference ke Iceberg."""


# ------------------------------------------------------------------
# Trino REST API helper (plain-text body)
# ------------------------------------------------------------------
def _trino_execute(sql):
    """
    Eksekusi satu SQL via Trino REST API, poll sampai selesai.

    Mengembalikan list-of-list (rows) untuk query SELECT/SHOW,
    atau list kosong untuk DDL/DML.
    """
    resp = requests.post(
        TRINO_URL,
        headers=_trino_headers(),
        data=sql.encode("utf-8"),
        timeout=TRINO_TIMEOUT,
    )
    if resp.status_code != 200:
        raise IcebergOutputError(
            f"Trino POST gagal (HTTP {resp.status_code}): {resp.text[:300]}"
        )

    result = resp.json()
    next_uri = result.get("nextUri")
    rows = []

    while next_uri:
        poll = requests.get(
            next_uri,
            headers={"X-Trino-User": TRINO_USER},
            timeout=TRINO_TIMEOUT,
        )
        result = poll.json()

        if "error" in result:
            msg = result["error"].get("message", str(result["error"]))
            raise IcebergOutputError(f"Trino error: {msg[:500]}")

        if "data" in result:
            rows = result["data"]

        next_uri = result.get("nextUri")

    return rows


def _trino_scalar(sql):
    """Eksekusi query dan kembalikan nilai kolom pertama baris pertama."""
    rows = _trino_execute(sql)
    if not rows:
        return None
    return rows[0][0]


# ------------------------------------------------------------------
# Excel -> Iceberg
# ------------------------------------------------------------------
def _read_excel(path):
    if not path.exists():
        raise IcebergOutputError(f"Excel sumber tidak ditemukan: {path}")
    pdf = pd.read_excel(path)
    logger.info(f"  Excel : {path.name} -> {len(pdf)} rows, {len(pdf.columns)} kolom")
    return pdf


def _trino_type(dtype):
    mapping = {
        "int64": "BIGINT",
        "int32": "INTEGER",
        "int": "INTEGER",
        "float64": "DOUBLE",
        "float32": "REAL",
        "bool": "BOOLEAN",
        "object": "VARCHAR",
    }
    return mapping.get(str(dtype), "VARCHAR")


def _escape_value(v):
    if pd.isna(v):
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return str(float(v))
    return "'" + str(v).replace("'", "''") + "'"


def _write_to_iceberg(pdf):
    """Recreate tabel Iceberg via Trino lalu INSERT batch dari DataFrame."""
    columns = list(pdf.columns)

    # 1. Drop & recreate (idempotent — data Excel diperbarui tiap run inference)
    _trino_execute(f"DROP TABLE IF EXISTS {target_table()}")

    col_defs = ", ".join(f"{c} {_trino_type(pdf[c].dtype)}" for c in columns)
    _trino_execute(f"CREATE TABLE {target_table()} ({col_defs}) WITH (format = 'PARQUET')")
    logger.info(f"  ✓ CREATE TABLE : {target_table()}")

    # 2. Batch INSERT
    total = len(pdf)
    col_list = ", ".join(columns)

    for start in range(0, total, BATCH_SIZE):
        batch = pdf.iloc[start:start + BATCH_SIZE]
        value_rows = []
        for _, row in batch.iterrows():
            vals = [_escape_value(row[c]) for c in columns]
            value_rows.append("(" + ", ".join(vals) + ")")

        values_sql = ", ".join(value_rows)
        _trino_execute(
            f"INSERT INTO {target_table()} ({col_list}) VALUES {values_sql}"
        )
        logger.info(
            f"    batch rows {start}-{min(start + BATCH_SIZE, total)} OK"
        )

    logger.info(f"  ✓ Data ditulis ke Iceberg : {target_table()} ({total} rows)")


def _validate_iceberg(expected_count):
    """Validasi tabel Iceberg setelah write: count, unique id, distribusi."""
    logger.info("=" * 60)
    logger.info("VALIDASI TABEL ICEBERG (INFERENCE MODEL UTAMA)")
    logger.info("=" * 60)

    total = int(_trino_scalar(f"SELECT COUNT(*) FROM {target_table()}"))
    distinct_id = int(
        _trino_scalar(
            f"SELECT COUNT(DISTINCT {IDENTIFIER_COLUMN}) FROM {target_table()}"
        )
    )

    null_counts = {}
    for c in REQUIRED_COLUMNS:
        null_counts[c] = int(
            _trino_scalar(f"SELECT COUNT(*) FROM {target_table()} WHERE {c} IS NULL")
        )
    total_null = sum(null_counts.values())

    dist_rows = _trino_execute(
        f"SELECT CAST(prediksi AS VARCHAR), COUNT(*) "
        f"FROM {target_table()} GROUP BY prediksi ORDER BY prediksi"
    )
    distribution = {row[0]: int(row[1]) for row in dist_rows}

    result = {
        "target_table": target_table(),
        "source_excel": str(excel_source()),
        "source_row_count": expected_count,
        "iceberg_row_count": total,
        "row_count_ok": total == expected_count,
        "unique_id_count": distinct_id,
        "unique_id_ok": distinct_id == total,
        "null_counts": null_counts,
        "null_count": total_null,
        "null_ok": total_null == 0,
        "schema_match": True,
        "missing_columns": [],
        "distribution": distribution,
        "status": "SUCCESS" if (
            total == expected_count
            and distinct_id == total
            and total_null == 0
        ) else "FAIL",
    }

    logger.info(
        f"  Row count     : {total} (source {expected_count}) "
        f"{'PASS' if result['row_count_ok'] else 'FAIL'}"
    )
    logger.info(
        f"  Unique id     : {distinct_id} "
        f"{'PASS' if result['unique_id_ok'] else 'FAIL'}"
    )
    logger.info(
        f"  NULL          : {total_null} "
        f"{'PASS' if result['null_ok'] else 'FAIL'}"
    )
    for label, count in sorted(distribution.items()):
        pct = (count / total) * 100 if total else 0
        logger.info(f"    prediksi={label:<3}: {count} ({pct:.2f}%)")

    return result


def _write_quality_report(report):
    path = log_dir() / "inference_iceberg_quality_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Quality report tersimpan : {path}")


def run_iceberg_output():
    """
    Orkestrator Tahap 6 — Iceberg Output untuk Model Utama.

    Baca Excel hasil inference -> recreate tabel -> INSERT batch
    -> validasi -> kumpulkan report -> tulis quality report.
    """
    logger.info("=" * 60)
    logger.info("TAHAP 6 — ICEBERG OUTPUT (EXCEL -> ICEBERG) MODEL UTAMA")
    logger.info("=" * 60)

    # 1. Read Excel
    pdf = _read_excel(excel_source())

    missing = [c for c in REQUIRED_COLUMNS if c not in pdf.columns]
    if missing:
        raise IcebergOutputError(f"Kolom wajib tidak ada di Excel: {missing}")

    # 2. Write to Iceberg
    _write_to_iceberg(pdf)

    # 3. Validate
    validation = _validate_iceberg(expected_count=len(pdf))

    # 4. Report
    report = {
        "tahap": "TAHAP_6_ICEBERG_OUTPUT_MODEL_UTAMA",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "catalog": "iceberg",
        "target": validation,
        "status": validation["status"],
    }

    _write_quality_report(report)

    return report


def reload_test():
    """Reload test: baca ulang tabel Iceberg, tampilkan count + sample."""
    logger.info("=" * 60)
    logger.info("RELOAD TEST — TABEL ICEBERG INFERENCE MODEL UTAMA")
    logger.info("=" * 60)

    total = int(_trino_scalar(f"SELECT COUNT(*) FROM {target_table()}"))
    sample_rows = _trino_execute(
        f"SELECT * FROM {target_table()} LIMIT 3"
    )

    logger.info(f"  {target_table():<55} : {total} rows")
    return {
        "table": target_table(),
        "count": total,
        "sample": sample_rows,
    }


def print_report(report):
    """Mencetak laporan akhir Tahap 6 — Iceberg Output Model Utama."""
    print()
    print("=" * 88)
    print("TAHAP 6 — ICEBERG OUTPUT MODEL UTAMA")
    print("=" * 88)

    t = report["target"]
    print("[INFERENCE RESULT MODEL UTAMA]")
    print(f"  Source excel   : {t['source_excel']}")
    print(f"  Iceberg table  : {t['target_table']}")
    print(
        f"  Row count      : {t['iceberg_row_count']} (source {t['source_row_count']}) "
        f"{'PASS' if t['row_count_ok'] else 'FAIL'}"
    )
    print(
        f"  Unique id      : {t['unique_id_count']} "
        f"{'PASS' if t['unique_id_ok'] else 'FAIL'}"
    )
    print(
        f"  NULL           : {t['null_count']} "
        f"{'PASS' if t['null_ok'] else 'FAIL'}"
    )
    for label, count in sorted(t.get("distribution", {}).items()):
        pct = (count / t["iceberg_row_count"]) * 100 if t["iceberg_row_count"] else 0
        print(f"    prediksi={label:<3}: {count} ({pct:.2f}%)")

    print("\n# STATUS")
    print(f"  {report['status']}")
    print(f"  Timestamp : {report['timestamp']}")
    print("=" * 88)


if __name__ == "__main__":
    run_iceberg_output()
