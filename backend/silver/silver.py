import re

from pyspark.sql.functions import col, trim

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def clean_column_name(column_name: str):
    """
    Membersihkan nama kolom agar konsisten.
    """

    column_name = column_name.strip().lower()
    column_name = column_name.replace(" ", "_")
    column_name = column_name.replace("-", "_")
    column_name = column_name.replace("/", "_")
    column_name = column_name.replace("(", "")
    column_name = column_name.replace(")", "")
    column_name = re.sub(r"[^a-zA-Z0-9_]", "", column_name)

    return column_name


def process_table(table_name: str):

    spark = get_spark("Silver Layer")

    logger.info("=" * 60)
    logger.info(f"Processing : {table_name}")

    # =====================================================
    # Membaca Bronze Layer
    # =====================================================

    df = spark.table(f"{ICEBERG_NAMESPACE}.bronze.{table_name}")

    logger.info(f"Rows Awal : {df.count()}")

    # =====================================================
    # Rename Kolom
    # =====================================================

    for column in df.columns:

        df = df.withColumnRenamed(
            column,
            clean_column_name(column)
        )

    # =====================================================
    # Trim Seluruh Kolom String
    # =====================================================

    for field in df.schema.fields:

        if field.dataType.simpleString() == "string":

            df = df.withColumn(
                field.name,
                trim(col(field.name))
            )

    # =====================================================
    # Menghapus Baris yang Seluruh Kolomnya Kosong
    # =====================================================

    df = df.na.drop(how="all")

    # =====================================================
    # Validasi Khusus Data Referensi Mahasiswa
    # =====================================================

    if table_name == "data_referensi_mahasiswa":

        logger.info("Validasi data mahasiswa...")

        # ---------------------------------
        # Hapus data tanpa tanggal masuk
        # ---------------------------------

        df = df.filter(
            col("tanggal_masuk").isNotNull()
        )

    logger.info(f"Rows Akhir : {df.count()}")

    # =====================================================
    # Simpan ke Silver Layer
    # =====================================================

    (
        df.writeTo(f"{ICEBERG_NAMESPACE}.silver.{table_name}")
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(f"✓ Silver berhasil : {table_name}")

    return df


def process_all_tables():

    spark = get_spark("Silver Layer")

    tables = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze")

    total = 0

    for row in tables.collect():

        process_table(row.tableName)

        total += 1

    logger.info("=" * 60)
    logger.info(f"Total Table Diproses : {total}")
    logger.info("=" * 60)

    spark.stop()
