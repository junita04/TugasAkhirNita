"""
Tahap 6 — Iceberg Output (Parquet -> Iceberg).

Membaca hasil inference yang SUDAH tersimpan sebagai Parquet biasa:
  * data/predictions/prediction_result_without_smote.parquet
  * data/predictions/prediction_result_with_smote.parquet
  * data/predictions/prediction_comparison.parquet

lalu menyimpannya sebagai tabel Apache Iceberg FINAL untuk downstream
(Trino/Superset):

  * local.feature_store.prediction_result_without_smote
  * local.feature_store.prediction_result_with_smote
  * local.feature_store.prediction_comparison

TIDAK melakukan training ulang, TIDAK mengubah hasil prediksi, TIDAK
menambahkan StandardScaler/SMOTE, dan TIDAK menyentuh pipeline Tahap 1-5.

Catatan (Windows): pembuatan tabel Iceberg BARU lewat
``writeTo().createOrReplace()`` saja memicu ``NativeIO$Windows.access0``
karena Iceberg memanggil ``findVersion``/``listStatus`` pada metadata dir yang
belum ada. Pola yang terbukti berhasil:
  1. ``CREATE TABLE IF NOT EXISTS ... USING iceberg`` via SQL
  2. lalu ``writeTo().createOrReplace()``
``spark.catalog.tableExists()`` TIDAK digunakan (ikut memicu error yang sama).
"""

import json
from datetime import datetime

import pandas as pd

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, LOG_DIR, PROJECT_ROOT
from backend.utils.logger import get_logger

logger = get_logger(__name__)

PREDICTION_DIR = PROJECT_ROOT / "data" / "predictions"

PARQUET_WITHOUT_SMOTE = PREDICTION_DIR / "prediction_result_without_smote.parquet"
PARQUET_WITH_SMOTE = PREDICTION_DIR / "prediction_result_with_smote.parquet"
PARQUET_COMPARISON = PREDICTION_DIR / "prediction_comparison.parquet"

TABLE_WITHOUT_SMOTE = (
    f"{ICEBERG_NAMESPACE}.feature_store.prediction_result_without_smote"
)
TABLE_WITH_SMOTE = (
    f"{ICEBERG_NAMESPACE}.feature_store.prediction_result_with_smote"
)
TABLE_COMPARISON = f"{ICEBERG_NAMESPACE}.feature_store.prediction_comparison"

IDENTIFIER_COLUMN = "id_mahasiswa"

TARGETS = [
    {
        "name": "prediction_result_without_smote",
        "parquet": PARQUET_WITHOUT_SMOTE,
        "table": TABLE_WITHOUT_SMOTE,
        "required_columns": [
            IDENTIFIER_COLUMN, "ip", "sks", "angkatan", "jumlah_mk",
            "prediksi_status_kelulusan", "probabilitas_prediksi",
            "prediction_timestamp", "model_version", "model_variant",
        ],
    },
    {
        "name": "prediction_result_with_smote",
        "parquet": PARQUET_WITH_SMOTE,
        "table": TABLE_WITH_SMOTE,
        "required_columns": [
            IDENTIFIER_COLUMN, "ip", "sks", "angkatan", "jumlah_mk",
            "prediksi_status_kelulusan", "probabilitas_prediksi",
            "prediction_timestamp", "model_version", "model_variant",
        ],
    },
    {
        "name": "prediction_comparison",
        "parquet": PARQUET_COMPARISON,
        "table": TABLE_COMPARISON,
        "required_columns": [
            IDENTIFIER_COLUMN, "prediction_without_smote",
            "prediction_with_smote",
        ],
    },
]


class IcebergOutputError(RuntimeError):
    """Error spesifik proses penyimpanan hasil inference ke Iceberg."""


def _spark_type(dtype):
    """Mapping pandas dtype -> Spark SQL type untuk DDL Iceberg."""
    mapping = {
        "int64": "long",
        "int32": "int",
        "int": "int",
        "float64": "double",
        "float32": "double",
        "bool": "boolean",
    }
    return mapping.get(str(dtype), "string")


def _ddl_for(pdf):
    """Menyusun definisi kolom (DDL) dari pandas DataFrame Parquet sumber."""
    columns = [f"{c} {_spark_type(pdf[c].dtype)}" for c in pdf.columns]
    return ", ".join(columns)


def _read_parquet(path):
    if not path.exists():
        raise IcebergOutputError(f"Parquet sumber tidak ditemukan: {path}")
    pdf = pd.read_parquet(path)
    logger.info(f"  Parquet : {path.name} -> {len(pdf)} rows, "
                f"{len(pdf.columns)} kolom")
    return pdf


def _create_table_if_not_exists(spark, table, pdf):
    """
    Pre-create tabel Iceberg via SQL bila belum ada.

    Menghindari ``spark.catalog.tableExists()`` dan ``writeTo()`` langsung ke
    tabel baru (crash NativeIO$Windows.access0 di Windows). ``IF NOT EXISTS``
    aman untuk tabel yang sudah ada (no-op).
    """
    ddl = _ddl_for(pdf)
    spark.sql(f"CREATE TABLE IF NOT EXISTS {table} ({ddl}) USING iceberg")
    logger.info(f"  ✓ CREATE TABLE IF NOT EXISTS : {table}")


def _write_to_iceberg(spark, table, pdf):
    """
    Menulis DataFrame ke tabel Iceberg dengan createOrReplace (idempotent).
    Setelah pre-create, ReplaceTable berjalan normal.
    """
    spark_df = spark.createDataFrame(pdf)
    spark_df.writeTo(table).using("iceberg").createOrReplace()
    logger.info(f"  ✓ Data ditulis ke Iceberg : {table}")


def _validate_iceberg(spark, target, expected_count):
    """
    Validasi tabel Iceberg setelah write:

    - row count sesuai Parquet sumber
    - unique id_mahasiswa (jika ada pada sumber)
    - NULL pada kolom penting
    - schema match (semua kolom Parquet ada di tabel Iceberg)
    """
    table = target["table"]
    name = target["name"]
    required = target["required_columns"]

    logger.info("=" * 60)
    logger.info(f"VALIDASI TABEL ICEBERG ({name.upper()})")
    logger.info("=" * 60)

    df = spark.table(table)
    total = df.count()

    iceberg_columns = set(df.columns)

    # Schema match: semua kolom sumber harus ada di tabel Iceberg
    missing_cols = [c for c in required if c not in iceberg_columns]
    schema_match = len(missing_cols) == 0

    # Unique id
    distinct_id = df.select(IDENTIFIER_COLUMN).distinct().count()

    # NULL pada kolom penting
    null_counts = {
        c: int(df.filter(df[c].isNull()).count())
        for c in required
    }
    total_null = sum(null_counts.values())

    distribution = {}
    if "prediksi_status_kelulusan" in iceberg_columns:
        dist_rows = (
            df.groupBy("prediksi_status_kelulusan")
            .count()
            .orderBy("prediksi_status_kelulusan")
            .collect()
        )
        distribution = {row[0]: int(row["count"]) for row in dist_rows}

    result = {
        "target_table": table,
        "source_parquet": str(target["parquet"]),
        "source_row_count": expected_count,
        "iceberg_row_count": total,
        "row_count_ok": total == expected_count,
        "unique_id_count": distinct_id,
        "unique_id_ok": distinct_id == total,
        "null_counts": null_counts,
        "null_count": total_null,
        "null_ok": total_null == 0,
        "schema_match": schema_match,
        "missing_columns": missing_cols,
        "distribution": distribution,
        "status": "SUCCESS" if (total == expected_count
                                and distinct_id == total
                                and total_null == 0
                                and schema_match) else "FAIL",
    }

    logger.info(f"  Row count     : {total} (source {expected_count}) "
                f"{'PASS' if result['row_count_ok'] else 'FAIL'}")
    logger.info(f"  Unique id     : {distinct_id} "
                f"{'PASS' if result['unique_id_ok'] else 'FAIL'}")
    logger.info(f"  NULL          : {total_null} "
                f"{'PASS' if result['null_ok'] else 'FAIL'}")
    logger.info(f"  Schema match  : {schema_match} (missing={missing_cols})")
    for label, count in sorted(distribution.items()):
        pct = (count / total) * 100 if total else 0
        logger.info(f"    {label:<14}: {count} ({pct:.2f}%)")

    return result


def run_iceberg_output():
    """
    Orkestrator Tahap 6 — Iceberg Output.

    Untuk setiap target: baca Parquet -> pre-create tabel -> write Iceberg
    -> validasi -> kumpulkan report -> tulis quality report.
    """
    logger.info("=" * 60)
    logger.info("TAHAP 6 — ICEBERG OUTPUT (PARQUET -> ICEBERG)")
    logger.info("=" * 60)

    spark = get_spark("Inference Iceberg Output")

    per_target = {}

    for target in TARGETS:
        pdf = _read_parquet(target["parquet"])

        _create_table_if_not_exists(spark, target["table"], pdf)
        _write_to_iceberg(spark, target["table"], pdf)

        validation = _validate_iceberg(spark, target, expected_count=len(pdf))

        per_target[target["name"]] = validation

    report = {
        "tahap": "TAHAP_6_ICEBERG_OUTPUT",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "catalog": ICEBERG_NAMESPACE,
        "targets": per_target,
        "status": "SUCCESS"
        if all(t["status"] == "SUCCESS" for t in per_target.values())
        else "FAIL",
    }

    _write_quality_report(report)

    return report


def _write_quality_report(report):
    """Menyimpan quality report khusus output Iceberg ke logs/."""
    path = LOG_DIR / "inference_iceberg_quality_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Quality report tersimpan : {path}")


def reload_test(spark):
    """
    Reload test: baca ulang ketiga tabel Iceberg, tampilkan count + sample.
    """
    logger.info("=" * 60)
    logger.info("RELOAD TEST — TABEL ICEBERG")
    logger.info("=" * 60)

    results = {}
    for target in TARGETS:
        df = spark.table(target["table"])
        total = df.count()
        sample = df.limit(3).toPandas().to_dict(orient="records")
        results[target["name"]] = {
            "table": target["table"],
            "count": total,
            "columns": sorted(df.columns),
            "sample": sample,
        }
        logger.info(f"  {target['name']:<30} : {total} rows")

    return results


def print_report(report):
    """Mencetak laporan akhir Tahap 6 — Iceberg Output."""
    print()
    print("=" * 88)
    print("TAHAP 6 — ICEBERG OUTPUT")
    print("=" * 88)

    for name, t in report["targets"].items():
        print(f"[{name.upper()}]")
        print(f"  Source parquet : {t['source_parquet']}")
        print(f"  Iceberg table  : {t['target_table']}")
        print(f"  Row count      : {t['iceberg_row_count']} (source {t['source_row_count']}) "
              f"{'PASS' if t['row_count_ok'] else 'FAIL'}")
        print(f"  Unique id      : {t['unique_id_count']} "
              f"{'PASS' if t['unique_id_ok'] else 'FAIL'}")
        print(f"  NULL           : {t['null_count']} "
              f"{'PASS' if t['null_ok'] else 'FAIL'}")
        print(f"  Schema match   : {t['schema_match']} "
              f"{'PASS' if t['schema_match'] else 'FAIL'}")
        for label, count in sorted(t.get("distribution", {}).items()):
            pct = (count / t["iceberg_row_count"]) * 100
            print(f"    {label:<14}: {count} ({pct:.2f}%)")
        print()

    print("# STATUS")
    print(f"  {report['status']}")
    print(f"  Timestamp : {report['timestamp']}")
    print("=" * 88)
