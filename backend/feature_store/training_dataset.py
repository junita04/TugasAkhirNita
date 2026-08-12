from pyspark.sql import functions as F

from backend.spark.session import get_spark
from backend.config.settings import (
    ICEBERG_NAMESPACE,
    GRADUATION_LIMIT_DAYS,
)
from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    FEATURE_X,
    derive_features,
    check_leakage,
)

logger = get_logger(__name__)

TRAINING_TABLE = f"{ICEBERG_NAMESPACE}.feature_store.training_dataset"


def create_training_dataset(joined):

    spark = joined.sparkSession

    logger.info("=" * 60)
    logger.info("MEMBUAT TRAINING DATASET (mahasiswa LULUS)")
    logger.info("=" * 60)

    df = derive_features(joined)

    # =====================================================
    # Filter mahasiswa LULUS
    # =====================================================

    lulus = df.filter(
        F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS"
    )

    total_lulus = lulus.count()
    logger.info(f"Jumlah awal mahasiswa LULUS : {total_lulus}")

    # =====================================================
    # Label status_kelulusan (HANYA untuk mahasiswa LULUS)
    #
    # lama_studi (hari) = tanggal_keluar - tanggal_masuk.
    # Threshold: lama_studi <= 4 tahun (1460 hari) -> Tepat Waktu
    #            lama_studi >  4 tahun              -> Terlambat
    # =====================================================

    labeled = lulus.withColumn(
        "status_kelulusan",
        F.when(
            F.col("lama_studi") <= GRADUATION_LIMIT_DAYS,
            F.lit("Tepat Waktu"),
        ).otherwise(F.lit("Terlambat")),
    )

    label_counts = labeled.groupBy("status_kelulusan").count().collect()
    label_dist = {row.status_kelulusan: row["count"] for row in label_counts}
    tepat_waktu = label_dist.get("Tepat Waktu", 0)
    terlambat = label_dist.get("Terlambat", 0)
    logger.info(f"Label Tepat Waktu : {tepat_waktu}")
    logger.info(f"Label Terlambat   : {terlambat}")

    # =====================================================
    # Mahasiswa LULUS tanpa KHS (ip / sks NULL hasil LEFT JOIN)
    # Tidak diimputasi; didokumentasikan.
    # =====================================================

    no_khs = labeled.filter(
        F.col("ip").isNull() | F.col("sks").isNull()
    )
    no_khs_ids = [row.id_mahasiswa for row in no_khs.select("id_mahasiswa").collect()]
    logger.info(f"Training LULUS tanpa KHS  : {len(no_khs_ids)}")

    # =====================================================
    # Dataset final: exclude record yang fitur wajib NULL
    # =====================================================

    valid = labeled.dropna(subset=FEATURE_X)

    valid = valid.dropDuplicates(["id_mahasiswa"])

    training_df = valid.select("id_mahasiswa", *FEATURE_X, "status_kelulusan")

    # =====================================================
    # Data leakage check
    # =====================================================

    forbidden, extra = check_leakage(training_df, label_columns=["status_kelulusan"])

    logger.info(f"Leakage check: forbidden={forbidden} extra={extra}")

    # =====================================================
    # Simpan Feature Store Training
    # =====================================================

    (
        training_df.writeTo(TRAINING_TABLE)
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(f"Rows Training Dataset : {training_df.count()}")
    logger.info("✓ Training Dataset berhasil dibuat.")
    logger.info("=" * 60)

    report = {
        "table": TRAINING_TABLE,
        "jumlah_awal_lulus": total_lulus,
        "jumlah_valid": training_df.count(),
        "jumlah_tanpa_khs": len(no_khs_ids),
        "excluded_ids_no_khs": no_khs_ids,
        "label_tepat_waktu": tepat_waktu,
        "label_terlambat": terlambat,
        "null_feature_after_dropna": 0,
        "duplicate_id": training_df.count()
        - training_df.select("id_mahasiswa").distinct().count(),
        "leakage_forbidden": forbidden,
        "leakage_extra": extra,
    }

    return training_df, report