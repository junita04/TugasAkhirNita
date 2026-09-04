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

TRAINING_TABLE = f"{ICEBERG_NAMESPACE}.feature_store.training_dataset"
TRAINING_TABLE_HIVE = "hive_iceberg.feature_store.training_dataset"


def create_training_dataset(joined):

    spark = joined.sparkSession

    logger.info("=" * 60)
    logger.info("MEMBUAT TRAINING DATASET (label IS NOT NULL)")
    logger.info("=" * 60)

    df = derive_features(joined)

    # =====================================================
    # Filter: hanya data yang memiliki label (0 atau 1)
    # Mahasiswa aktif 2022-2024 tidak boleh masuk training
    # =====================================================

    labeled = df.filter(F.col("label").isNotNull())

    total_labeled = labeled.count()
    logger.info(f"Jumlah awal dengan label : {total_labeled}")

    # =====================================================
    # Distribusi label
    # =====================================================

    label_counts = labeled.groupBy("label").count().collect()
    label_dist = {row.label: row["count"] for row in label_counts}
    tepat_waktu = label_dist.get(0, 0)
    terlambat = label_dist.get(1, 0)
    logger.info(f"Label 0 (Tepat Waktu) : {tepat_waktu}")
    logger.info(f"Label 1 (Terlambat)   : {terlambat}")

    # =====================================================
    # TRAINING DATA AUDIT - IP NULL
    # =====================================================

    total_sebelum_ip_filter = labeled.count()
    ip_null = labeled.filter(F.col("ip").isNull()).count()
    ip_null_ids = [row.id_mahasiswa for row in labeled.filter(F.col("ip").isNull()).select("id_mahasiswa").collect()]

    logger.info("TRAINING DATA AUDIT")
    logger.info(f"Training sebelum filtering : {total_sebelum_ip_filter}")
    logger.info(f"IP NULL                    : {ip_null}")

    # =====================================================
    # Dataset final: exclude record yang fitur wajib NULL
    # (termasuk IP NULL)
    # =====================================================

    valid = labeled.dropna(subset=FEATURE_X)

    total_sesudah_ip_filter = valid.count()
    logger.info(f"Training setelah filtering : {total_sesudah_ip_filter}")
    logger.info(f"Selisih (dikeluarkan)      : {total_sebelum_ip_filter - total_sesudah_ip_filter}")

    valid = valid.dropDuplicates(["id_mahasiswa"])

    training_df = valid.select("id_mahasiswa", *FEATURE_X, "label")

    # =====================================================
    # Data leakage check
    # =====================================================

    forbidden, extra = check_leakage(training_df, label_columns=["label"])

    logger.info(f"Leakage check: forbidden={forbidden} extra={extra}")

    # =====================================================
    # Simpan Feature Store Training
    # =====================================================

    (
        training_df.writeTo(TRAINING_TABLE)
        .using("iceberg")
        .createOrReplace()
    )

    # Write to HMS-backed catalog for Trino visibility
    (
        training_df.writeTo(TRAINING_TABLE_HIVE)
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(f"Rows Training Dataset : {training_df.count()}")
    logger.info("✓ Training Dataset berhasil dibuat.")
    logger.info("=" * 60)

    report = {
        "table": TRAINING_TABLE,
        "jumlah_awal_labeled": total_labeled,
        "jumlah_ip_null_dikeluarkan": ip_null,
        "ip_null_ids": ip_null_ids,
        "jumlah_valid": training_df.count(),
        "label_0_tepat_waktu": tepat_waktu,
        "label_1_terlambat": terlambat,
        "null_feature_after_dropna": 0,
        "duplicate_id": training_df.count()
        - training_df.select("id_mahasiswa").distinct().count(),
        "leakage_forbidden": forbidden,
        "leakage_extra": extra,
        "feature_columns": FEATURE_X,
    }

    return training_df, report
