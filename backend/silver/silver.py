import json
import re
from pathlib import Path

from pyspark.sql import functions as F

from backend.config.settings import ICEBERG_NAMESPACE, LOG_DIR
from backend.spark.session import get_spark
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================
# Spesifikasi Silver per sumber Bronze.
#   bronze_table -> (silver_table, peta kolom sumber -> target)
# Nama kolom dinormalisasi di SILVER; Bronze tetap raw.
# ============================================================

SILVER_SPECS = {
    "data_referensi_mahasiswa": (
        "silver_mahasiswa",
        {
            "ID": "id_mahasiswa",
            "ID_MHS": "id_mahasiswa",
            "Jenis Kelamin": "jenis_kelamin",
            "Tanggal Masuk": "tanggal_masuk",
            "Tanggal Keluar": "tanggal_keluar",
            "IPK": "ipk",
            "Total SKS": "total_sks",
            "Jumlah MK": "jumlah_mk",
            "Status Mahasiswa": "status_mahasiswa",
        },
    ),
    "data_khs": (
        "silver_khs",
        {"ID": "id_mahasiswa", "ID_MHS": "id_mahasiswa", "IP": "ip", "SKS": "sks"},
    ),
    "data_program_studi": (
        "silver_program_studi",
        {
            "Kode": "kode",
            "Nama Program Studi": "nama_program_studi",
            "Jumlah Dosen": "jumlah_dosen",
        },
    ),
    "data_kelas": (
        "silver_kelas",
        {"nama_kelas": "nama_kelas", "nama_mk": "nama_mk", "kuota": "kuota"},
    ),
    "data_kurikulum": (
        "silver_kurikulum",
        {
            "Nama Kurikulum": "nama_kurikulum",
            "Jumlah SKS Total": "jumlah_sks_total",
        },
    ),
}

VALID_STATUSES = {
    "AKTIF",
    "LULUS",
    "DIKELUARKAN",
    "MENGUNDURKAN DIRI",
    "LAINNYA",
    "WAFAT",
}


def clean_column_name(column_name: str):
    column_name = column_name.strip().lower()
    column_name = column_name.replace(" ", "_")
    column_name = column_name.replace("-", "_")
    column_name = column_name.replace("/", "_")
    column_name = column_name.replace("(", "")
    column_name = column_name.replace(")", "")
    column_name = re.sub(r"[^a-zA-Z0-9_]", "", column_name)
    return column_name


def _apply_column_map(df, mapping):
    lookup = {key.strip().lower(): value for key, value in mapping.items()}
    new_names = {
        column: lookup.get(column.strip().lower(), clean_column_name(column))
        for column in df.columns
    }
    for old, new in new_names.items():
        if old != new:
            df = df.withColumnRenamed(old, new)
    return df


def _trim_string_columns(df):
    for field in df.schema.fields:
        if field.dataType.simpleString() == "string":
            df = df.withColumn(field.name, F.trim(F.col(field.name)))
    return df


def _table_exists(spark, table_name):
    tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze")
    return any(row.tableName == table_name for row in tables.collect())


def _normalize_status(df):
    return df.withColumn(
        "status_mahasiswa_normalized",
        F.upper(F.trim(F.col("status_mahasiswa"))),
    )


def process_mahasiswa(df, report):
    logger.info("- Validasi Silver Mahasiswa")

    df = df.withColumn("tanggal_masuk", F.col("tanggal_masuk").cast("date"))
    df = df.withColumn("tanggal_keluar", F.col("tanggal_keluar").cast("date"))
    df = df.withColumn("ipk", F.col("ipk").cast("double"))
    df = df.withColumn("total_sks", F.col("total_sks").cast("int"))
    df = df.withColumn("jumlah_mk", F.col("jumlah_mk").cast("int"))

    awal = df.count()

    dup_id = awal - df.select("id_mahasiswa").distinct().count()
    null_id = df.filter(F.col("id_mahasiswa").isNull()).count()
    null_tanggal_masuk = df.filter(F.col("tanggal_masuk").isNull()).count()
    keluar_masuk_rusak = df.filter(
        F.col("tanggal_masuk").isNotNull()
        & F.col("tanggal_keluar").isNotNull()
        & (F.col("tanggal_keluar") < F.col("tanggal_masuk"))
    ).count()
    ipk_oor = df.filter(
        F.col("ipk").isNotNull() & ((F.col("ipk") < 0) | (F.col("ipk") > 4))
    ).count()
    ipk_null = df.filter(F.col("ipk").isNull()).count()
    total_sks_negatif = df.filter(
        F.col("total_sks").isNotNull() & (F.col("total_sks") < 0)
    ).count()
    jumlah_mk_negatif = df.filter(
        F.col("jumlah_mk").isNotNull() & (F.col("jumlah_mk") < 0)
    ).count()

    df_stat = _normalize_status(df)
    status_unknown = df_stat.filter(
        ~F.col("status_mahasiswa_normalized").isin(*sorted(VALID_STATUSES))
    ).count()

    extra = {
        "duplicate_id": dup_id,
        "null_id": null_id,
        "null_tanggal_masuk": null_tanggal_masuk,
        "keluar_sebelum_masuk": keluar_masuk_rusak,
        "ipk_out_of_range": ipk_oor,
        "ipk_null": ipk_null,
        "total_sks_negatif": total_sks_negatif,
        "jumlah_mk_negatif": jumlah_mk_negatif,
        "status_unknown": status_unknown,
    }

    excluded = df.filter(F.col("tanggal_masuk").isNull())
    excluded_ids = [row[0] for row in excluded.select("id_mahasiswa").collect()]

    kept = (
        df.filter(F.col("tanggal_masuk").isNotNull())
        .filter(
            ~(
                F.col("tanggal_keluar").isNotNull()
                & (F.col("tanggal_keluar") < F.col("tanggal_masuk"))
            )
        )
        .drop("status_mahasiswa_normalized")
    )

    if ipk_oor:
        kept = kept.filter(F.col("ipk").isNull() | ((F.col("ipk") >= 0) & (F.col("ipk") <= 4)))

    report.update(
        {
            "jumlah_awal": awal,
            "jumlah_valid": kept.count(),
            "invalid_detail": extra,
            "excluded_ids": excluded_ids,
        }
    )

    return kept


def process_khs(df, report):
    logger.info("- Validasi Silver KHS")

    df = df.withColumn("ip", F.col("ip").cast("double"))
    df = df.withColumn("sks", F.col("sks").cast("int"))

    awal = df.count()

    dup_id = awal - df.select("id_mahasiswa").distinct().count()
    null_id = df.filter(F.col("id_mahasiswa").isNull()).count()
    null_ip = df.filter(F.col("ip").isNull()).count()
    null_sks = df.filter(F.col("sks").isNull()).count()
    ip_negatif = df.filter(F.col("ip").isNotNull() & (F.col("ip") < 0)).count()
    ip_over = df.filter(F.col("ip").isNotNull() & (F.col("ip") > 4)).count()
    sks_negatif = df.filter(F.col("sks").isNotNull() & (F.col("sks") < 0)).count()
    ip_nol = df.filter(F.col("ip").isNotNull() & (F.col("ip") == 0)).count()
    sks_nol = df.filter(F.col("sks").isNotNull() & (F.col("sks") == 0)).count()

    extra = {
        "duplicate_id": dup_id,
        "null_id": null_id,
        "null_ip": null_ip,
        "null_sks": null_sks,
        "ip_negatif": ip_negatif,
        "ip_atas_4": ip_over,
        "sks_negatif": sks_negatif,
        "ip_sama_dengan_nol": ip_nol,
        "sks_sama_dengan_nol": sks_nol,
    }

    kept = df.filter(
        F.col("id_mahasiswa").isNotNull()
        & F.col("ip").isNotNull()
        & F.col("sks").isNotNull()
        & (F.col("ip") >= 0)
        & (F.col("ip") <= 4)
        & (F.col("sks") >= 0)
    )

    report.update(
        {
            "jumlah_awal": awal,
            "jumlah_valid": kept.count(),
            "invalid_detail": extra,
            "excluded_ids": [],
        }
    )

    return kept


def process_table(table_name: str):

    spark = get_spark("TugasAkhirNita - Silver Layer")

    if table_name not in SILVER_SPECS:
        logger.warning(f"Tabel bronze '{table_name}' tidak memiliki spesifikasi Silver. Skip.")
        return None

    if not _table_exists(spark, table_name):
        logger.warning(f"Tabel bronze '{table_name}' tidak ada. Skip.")
        return None

    silver_name, column_map = SILVER_SPECS[table_name]

    logger.info("=" * 60)
    logger.info(f"Processing : {table_name} -> {silver_name}")
    logger.info("=" * 60)

    df = spark.table(f"{ICEBERG_NAMESPACE}.bronze.{table_name}")

    logger.info(f"Rows Bronze : {df.count()}")

    df = _apply_column_map(df, column_map)
    df = _trim_string_columns(df)
    df = df.na.drop(how="all")

    report = {
        "silver_table": silver_name,
        "jumlah_awal": df.count(),
        "jumlah_valid": df.count(),
        "invalid_detail": {},
        "excluded_ids": [],
    }

    if table_name == "data_referensi_mahasiswa":
        df = process_mahasiswa(df, report)
    elif table_name == "data_khs":
        df = process_khs(df, report)

    df.writeTo(f"{ICEBERG_NAMESPACE}.silver.{silver_name}") \
        .using("iceberg") \
        .createOrReplace()

    logger.info(f"Rows Silver : {df.count()}")
    logger.info(f"OK Silver : {silver_name}")

    return df, report


def build_quality_report(reports):
    spark = get_spark("TugasAkhirNita - Quality Report")

    report = {
        "tables": reports,
        "join_referensi_khs": {},
    }

    mahasiswa_report = next(
        (r for r in reports if r["silver_table"] == "silver_mahasiswa"), None
    )
    khs_report = next(
        (r for r in reports if r["silver_table"] == "silver_khs"), None
    )

    if mahasiswa_report and khs_report:
        ref_ids = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa") \
            .select("id_mahasiswa").distinct().count()
        khs_ids = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_khs") \
            .select("id_mahasiswa").distinct().count()

        ref_all = set(
            row[0]
            for row in spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa")
            .select("id_mahasiswa").collect()
        )
        khs_all = set(
            row[0]
            for row in spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_khs")
            .select("id_mahasiswa").collect()
        )

        report["join_referensi_khs"] = {
            "silver_mahasiswa_unique_id": ref_ids,
            "silver_khs_unique_id": khs_ids,
            "khs_id_tidak_ada_di_referensi": len(khs_all - ref_all),
            "referensi_tanpa_khs": len(ref_all - khs_all),
            "referensi_ada_khs": len(ref_all & khs_all),
        }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = LOG_DIR / "data_quality_report.json"

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Data Quality Report tersimpan : {json_path}")

    return report


def print_quality_report(report):
    print()
    print("=" * 88)
    print("DATA QUALITY REPORT - SILVER")
    print("=" * 88)
    header = (
        f"{'Dataset':<24}{'Awal':>8}{'Valid':>9}{'Missing/Inval':>15}{'Dikeluarkan':>13}"
    )
    print(header)
    print("-" * 88)
    for tb in report["tables"]:
        invalid = tb.get("invalid_detail", {})
        detail_total = sum(
            value
            for key, value in invalid.items()
            if key not in {"ip_sama_dengan_nol", "sks_sama_dengan_nol"}
        )
        excluded = int(tb["jumlah_awal"]) - int(tb["jumlah_valid"])
        print(
            f"{tb['silver_table']:<24}{tb['jumlah_awal']:>8}{tb['jumlah_valid']:>9}"
            f"{detail_total:>15}{excluded:>13}"
        )
    print("-" * 88)

    khs = next((r for r in report["tables"] if r["silver_table"] == "silver_khs"), None)
    if khs:
        print("Catatan IP == 0 (dipertahankan, bukan missing): "
              f"{khs['invalid_detail']['ip_sama_dengan_nol']}")
        print("Catatan SKS == 0 (dipertahankan): "
              f"{khs['invalid_detail']['sks_sama_dengan_nol']}")

    print()
    print("JOIN REFERENSI <-> KHS (level Silver)")
    jk = report["join_referensi_khs"]
    for key, value in jk.items():
        print(f"  {key:<34}: {value}")

    print()
    mahasiswa = next(
        (r for r in report["tables"] if r["silver_table"] == "silver_mahasiswa"), None
    )
    if mahasiswa and mahasiswa["excluded_ids"]:
        print("Mahasiswa dikeluarkan (tanggal_masuk kosong / data tidak lengkap):")
        print(f"  jumlah : {len(mahasiswa['excluded_ids'])}")
        print(f"  contoh : {mahasiswa['excluded_ids'][:10]}")
    print("=" * 88)


def process_all_tables():

    spark = get_spark("TugasAkhirNita - Silver Layer")

    reports = []

    for bronze_table in SILVER_SPECS:
        result = process_table(bronze_table)
        if result is None:
            continue
        _, report = result
        reports.append(report)

    quality_report = build_quality_report(reports)
    print_quality_report(quality_report)

    return reports