from pyspark.sql.functions import col, upper, trim

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_training_dataset():

    spark = get_spark("Feature Store")

    logger.info("=" * 60)
    logger.info("MEMBUAT TRAINING DATASET")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Gold Mahasiswa
    # =====================================================

    df = spark.table(f"{ICEBERG_NAMESPACE}.gold.gold_mahasiswa")

    logger.info(f"Rows Gold : {df.count()}")

    # =====================================================
    # Distribusi Status Mahasiswa
    # =====================================================

    logger.info("Distribusi Status Mahasiswa")

    df.groupBy("status_mahasiswa") \
        .count() \
        .show(truncate=False)

    # =====================================================
    # Filter Mahasiswa Lulus
    # =====================================================

    df = df.filter(
        upper(trim(col("status_mahasiswa"))) == "LULUS"
    )

    logger.info(f"Mahasiswa Lulus : {df.count()}")

    # =====================================================
    # Distribusi Status Kelulusan
    # =====================================================

    logger.info("Distribusi Status Kelulusan")

    df.groupBy("status_kelulusan") \
        .count() \
        .show(truncate=False)

    # =====================================================
    # Menghapus Data yang Feature / Label NULL
    # =====================================================

    df = df.dropna(
        subset=[
            "jenis_kelamin",
            "estimasi_semester",
            "ipk",
            "total_sks",
            "jumlah_mk",
            "persentase_sks",
            "status_kelulusan"
        ]
    )

    logger.info(f"Rows Siap Training : {df.count()}")

    # =====================================================
    # Memilih Feature dan Label
    # =====================================================

    training_df = df.select(
        "jenis_kelamin",
        "estimasi_semester",
        "ipk",
        "total_sks",
        "jumlah_mk",
        "persentase_sks",
        "status_kelulusan"
    )

    logger.info(f"Jumlah Feature : {len(training_df.columns) - 1}")
    logger.info(f"Jumlah Kolom : {len(training_df.columns)}")

    # =====================================================
    # Distribusi Label Training
    # =====================================================

    logger.info("Distribusi Label Training")

    training_df.groupBy("status_kelulusan") \
        .count() \
        .show(truncate=False)

    logger.info(f"Rows Training Dataset : {training_df.count()}")

    # =====================================================
    # Simpan ke Feature Store
    # =====================================================

    (
        training_df.writeTo(
            f"{ICEBERG_NAMESPACE}.feature_store.training_dataset"
        )
        .using("iceberg")
        .createOrReplace()
    )

    logger.info("✓ Training Dataset berhasil dibuat.")
    logger.info("=" * 60)

    return training_df
