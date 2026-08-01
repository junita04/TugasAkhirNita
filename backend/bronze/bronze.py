from pathlib import Path

import pandas as pd

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def excel_sheet_to_table(sheet_name: str) -> str:
    """
    Mengubah nama sheet menjadi nama tabel Iceberg.
    """

    return (
        sheet_name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def load_all_sheets_to_bronze(file_path: Path):

    logger.info("=" * 60)
    logger.info("MEMULAI BRONZE LAYER")
    logger.info("=" * 60)

    spark = get_spark("Bronze Layer")

    excel = pd.ExcelFile(file_path)

    success_tables = []
    skipped_sheets = []

    logger.info(f"Total Sheet : {len(excel.sheet_names)}")

    for sheet in excel.sheet_names:

        logger.info("-" * 60)
        logger.info(f"Sheet : {sheet}")

        # ===================================================
        # CEK DENGAN PANDAS DULU
        # ===================================================

        try:

            preview = pd.read_excel(
                file_path,
                sheet_name=sheet
            )

        except Exception as e:

            logger.warning(f"Gagal membaca sheet '{sheet}'")
            logger.warning(str(e))

            skipped_sheets.append(sheet)

            continue

        # ===================================================
        # SKIP JIKA TIDAK ADA DATA
        # ===================================================

        if preview.empty:

            logger.warning(f"Sheet '{sheet}' kosong. Skip.")

            skipped_sheets.append(sheet)

            continue

        # ===================================================
        # SKIP JIKA TIDAK ADA KOLOM
        # ===================================================

        if len(preview.columns) == 0:

            logger.warning(f"Sheet '{sheet}' tidak memiliki kolom. Skip.")

            skipped_sheets.append(sheet)

            continue

        # ===================================================
        # BACA DENGAN SPARK
        # ===================================================

        df = (
            spark.read
            .format("com.crealytics.spark.excel")
            .option("header", "true")
            .option("inferSchema", "true")
            .option("dataAddress", f"'{sheet}'!A1")
            .load(str(file_path))
        )

        table_name = excel_sheet_to_table(sheet)

        logger.info(f"Table : {table_name}")
        logger.info(f"Rows  : {df.count()}")
        logger.info(f"Cols  : {len(df.columns)}")

        df.printSchema()

        (
            df.writeTo(f"{ICEBERG_NAMESPACE}.bronze.{table_name}")
            .using("iceberg")
            .createOrReplace()
        )

        logger.info(f"✓ Berhasil -> {ICEBERG_NAMESPACE}.bronze.{table_name}")

        success_tables.append(table_name)

    logger.info("=" * 60)
    logger.info("BRONZE SUMMARY")
    logger.info("=" * 60)

    logger.info(f"Total Berhasil : {len(success_tables)}")

    for table in success_tables:
        logger.info(f"✓ {table}")

    logger.info("")

    logger.info(f"Total Skip : {len(skipped_sheets)}")

    for sheet in skipped_sheets:
        logger.info(f"- {sheet}")

    logger.info("=" * 60)
