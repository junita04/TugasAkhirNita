from pathlib import Path
import gc
import time

import pandas as pd

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Pemetaan sheet sumber -> nama tabel Bronze.
EXPECTED_SHEETS_TO_TABLE = {
    "Referensi Data Mahasiswa": "data_referensi_mahasiswa",
    "Data KHS": "data_khs",
    "Data Program Studi": "data_program_studi",
    "Data Mata Kuliah": "data_mata_kuliah",
    "Data Kelas": "data_kelas",
    "Data Kurikulum": "data_kurikulum",
}


def excel_sheet_to_table(sheet_name: str) -> str:
    return (
        sheet_name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def _validate_sheet_pandas(file_path: Path, sheet: str) -> pd.DataFrame | None:
    try:
        preview = pd.read_excel(file_path, sheet_name=sheet)
    except Exception as e:
        logger.warning(f"Gagal membaca sheet '{sheet}' via pandas: {e}")
        return None

    if preview.empty:
        logger.warning(f"SKIP: Sheet '{sheet}' kosong, tidak diproses.")
        return None

    if len(preview.columns) == 0:
        logger.warning(f"SKIP: Sheet '{sheet}' tidak memiliki kolom.")
        return None

    if len(preview) == 0:
        logger.warning(f"SKIP: Sheet '{sheet}' hanya memiliki header tanpa data.")
        return None

    return preview


def _write_sheet(spark, file_path: Path, sheet: str, table_name: str):
    """
    Membaca satu sheet via Spark Excel, lalu tulis ke Iceberg bronze table.
    Mengembalikan (row_count, col_count).
    """
    full_table = f"{ICEBERG_NAMESPACE}.bronze.{table_name}"

    df = (
        spark.read
        .format("com.crealytics.spark.excel")
        .option("header", "true")
        .option("inferSchema", "true")
        .option("dataAddress", f"'{sheet}'!A1")
        .load(str(file_path))
    )

    df = df.coalesce(1)
    row_count = df.count()
    col_count = len(df.columns)

    spark.sql(f"DROP TABLE IF EXISTS {full_table}")

    (
        df.write
        .format("iceberg")
        .mode("overwrite")
        .saveAsTable(full_table)
    )

    return row_count, col_count, full_table


def load_all_sheets_to_bronze(file_path: Path):
    """
    Load semua sheet Excel ke Iceberg bronze tables.

    Strategi memory: stop + buat ulang SparkSession untuk SETIAP sheet.
    Ini memastikan JVM heap (1g) dibersihkan sepenuhnya antar sheet,
    mencegah OutOfMemoryError yang terjadi saat write Iceberg bertumpuk
    dalam satu JVM yang sama.
    """
    logger.info("=" * 60)
    logger.info("BRONZE LAYER")
    logger.info("=" * 60)

    excel = pd.ExcelFile(file_path)

    success_tables = []
    skipped_sheets = []
    failed_sheets = []

    logger.info(f"Total sheet: {len(excel.sheet_names)}")

    # --- Tahap 1: Validasi semua sheet via pandas (ringan, tanpa JVM) ---
    valid_sheets: list[tuple[str, str]] = []

    for sheet in excel.sheet_names:
        logger.info("-" * 60)
        logger.info(f"Validating sheet: {sheet}")

        preview = _validate_sheet_pandas(file_path, sheet)
        if preview is None:
            skipped_sheets.append(sheet)
            continue

        rows_detected = len(preview)
        logger.info(f"Rows detected: {rows_detected}")

        table_name = EXPECTED_SHEETS_TO_TABLE.get(
            sheet.strip(), excel_sheet_to_table(sheet)
        )
        valid_sheets.append((sheet, table_name))

    # --- Tahap 2: Proses setiap sheet dengan SparkSession yang terisolasi ---
    for sheet, table_name in valid_sheets:
        logger.info("-" * 60)
        logger.info(f"Processing sheet: {sheet}")

        spark = None
        try:
            # Buat SparkSession baru (fresh JVM) untuk setiap sheet
            spark = get_spark(f"TugasAkhirNita - Bronze ({sheet})")

            row_count, col_count, full_table = _write_sheet(
                spark, file_path, sheet, table_name
            )

            logger.info(f"Table     : {table_name}")
            logger.info(f"Spark rows: {row_count}")
            logger.info(f"Spark cols: {col_count}")
            logger.info(f"Status: SUCCESS -> {full_table}")
            success_tables.append(table_name)

        except Exception as e:
            logger.error(f"Status: FAILED - {type(e).__name__}: {e}")
            failed_sheets.append(sheet)

        finally:
            # SELALU stop SparkSession agar JVM memory (1g) dibersihkan
            # sepenuhnya sebelum sheet berikutnya.
            if spark is not None:
                try:
                    spark.stop()
                except Exception:
                    pass
                # Force garbage collection + delay agar JVM benar-benar
                # release memory sebelum session baru dibuat.
                gc.collect()
                time.sleep(2)

    # --- Summary ---
    logger.info("=" * 60)
    logger.info("Bronze processing completed.")
    logger.info(f"Successful sheets: {len(success_tables)}")
    logger.info(f"Skipped sheets   : {len(skipped_sheets)}")
    logger.info(f"Failed sheets    : {len(failed_sheets)}")
    logger.info("=" * 60)

    if success_tables:
        logger.info("Berhasil:")
        for t in success_tables:
            logger.info(f"  OK  {t}")

    if skipped_sheets:
        logger.info("Dilewati (kosong/tidak valid):")
        for s in skipped_sheets:
            logger.info(f"  SKIP  {s}")

    if failed_sheets:
        logger.error("Gagal (error saat load Spark):")
        for f in failed_sheets:
            logger.error(f"  FAIL  {f}")

    expected = set(EXPECTED_SHEETS_TO_TABLE.values())
    ingested = set(success_tables)
    not_ingested = expected - ingested

    if not_ingested:
        logger.warning(
            f"Sheet wajib tidak terbentuk (mungkin kosong/tidak ada): {sorted(not_ingested)}"
        )

    return success_tables, skipped_sheets
