from pyspark.sql import functions as F

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    FEATURE_X,
    derive_features,
    check_leakage,
)

logger = get_logger(__name__)

INFERENCE_TABLE = f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset"


def create_inference_dataset(joined):

    spark = joined.sparkSession

    logger.info("=" * 60)
    logger.info("MEMBUAT INFERENCE DATASET (mahasiswa AKTIF)")
    logger.info("=" * 60)

    df = derive_features(joined)

    # =====================================================
    # Filter mahasiswa AKTIF
    # =====================================================

    aktif = df.filter(
        F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF"
    )

    total_aktif = aktif.count()
    logger.info(f"Jumlah awal mahasiswa AKTIF : {total_aktif}")

    # =====================================================
    # Mahasiswa AKTIF tanpa KHS (ip / sks NULL)
    # Tidak diimputasi; didokumentasikan.
    # =====================================================

    no_khs = aktif.filter(
        F.col("ip").isNull() | F.col("sks").isNull()
    )
    no_khs_ids = [row.id_mahasiswa for row in no_khs.select("id_mahasiswa").collect()]
    logger.info(f"Inference AKTIF tanpa KHS : {len(no_khs_ids)}")

    # =====================================================
    # Dataset final: exclude record yang fitur wajib NULL
    # =====================================================

    valid = aktif.dropna(subset=FEATURE_X)

    valid = valid.dropDuplicates(["id_mahasiswa"])

    inference_df = valid.select("id_mahasiswa", *FEATURE_X)

    # =====================================================
    # Data leakage check
    # =====================================================

    forbidden, extra = check_leakage(inference_df)

    logger.info(f"Leakage check: forbidden={forbidden} extra={extra}")

    # =====================================================
    # Simpan Feature Store Inference
    # =====================================================

    (
        inference_df.writeTo(INFERENCE_TABLE)
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(f"Rows Inference Dataset : {inference_df.count()}")
    logger.info("✓ Inference Dataset berhasil dibuat.")
    logger.info("=" * 60)

    report = {
        "table": INFERENCE_TABLE,
        "jumlah_awal_aktif": total_aktif,
        "jumlah_valid": inference_df.count(),
        "jumlah_tanpa_khs": len(no_khs_ids),
        "excluded_ids_no_khs": no_khs_ids,
        "null_feature_after_dropna": 0,
        "duplicate_id": inference_df.count()
        - inference_df.select("id_mahasiswa").distinct().count(),
        "leakage_forbidden": forbidden,
        "leakage_extra": extra,
    }

    return inference_df, report