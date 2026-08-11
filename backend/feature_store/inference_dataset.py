from pyspark.sql.functions import col, upper, trim

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def create_inference_dataset():

    spark = get_spark("Feature Store")

    logger.info("=" * 60)
    logger.info("MEMBUAT INFERENCE DATASET")
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
    # Filter Mahasiswa Aktif
    # =====================================================

    df = df.filter(
        upper(trim(col("status_mahasiswa"))) == "AKTIF"
    )

    logger.info(f"Mahasiswa Aktif : {df.count()}")

    # =====================================================
    # Menghapus Data yang Feature NULL
    # =====================================================

    df = df.dropna(
        subset=[
            "jenis_kelamin",
            "estimasi_semester",
            "ipk",
            "total_sks",
            "jumlah_mk",
            "persentase_sks"
        ]
    )

    logger.info(f"Rows Siap Inference : {df.count()}")

    # =====================================================
    # Memilih Feature
    #
    # Enam fitur model identik dengan training. Jika kolom identitas
    # mahasiswa (nim) tersedia di Gold, kolom tersebut dipertahankan
    # sebagai identifier (bukan fitur model) agar hasil prediksi dapat
    # diperagakan per-mahasiswa pada dashboard Superset.
    # =====================================================

    feature_columns = [
        "jenis_kelamin",
        "estimasi_semester",
        "ipk",
        "total_sks",
        "jumlah_mk",
        "persentase_sks"
    ]

    select_columns = [
        column for column in ("nim",) + tuple(feature_columns)
        if column in df.columns
    ]

    inference_df = df.select(*select_columns)

    logger.info(f"Jumlah Feature : {len(feature_columns)}")
    logger.info(f"Rows Inference Dataset : {inference_df.count()}")

    # =====================================================
    # Simpan ke Feature Store
    # =====================================================

    (
        inference_df.writeTo(
            f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset"
        )
        .using("iceberg")
        .createOrReplace()
    )

    logger.info("✓ Inference Dataset berhasil dibuat.")
    logger.info("=" * 60)

    return inference_df
