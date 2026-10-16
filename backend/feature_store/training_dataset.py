from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.config.namespaces import table
from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    FEATURE_X,
    derive_features,
    derive_ipk_kategori,
    check_leakage,
)

logger = get_logger(__name__)

# Angkatan training
TRAINING_ANGKATAN = list(range(2012, 2022))  # 2012-2021


def create_training_dataset(joined):

    spark = joined.sparkSession

    logger.info("=" * 60)
    logger.info("MEMBUAT TRAINING DATASET (ANGKATAN 2012-2021)")
    logger.info("=" * 60)

    df = derive_features(joined)
    df = derive_ipk_kategori(df)

    # =====================================================
    # Filter: angkatan 2012-2021 (lulus + aktif)
    # =====================================================

    angkatan_df = df.filter(F.col("angkatan").isin(TRAINING_ANGKATAN))

    total_angkatan = angkatan_df.count()
    logger.info(f"Jumlah angkatan 2012-2021 : {total_angkatan}")

    # =====================================================
    # Hitung jumlah lulus vs aktif
    # =====================================================

    status_dist = angkatan_df.groupBy("status_mahasiswa").count().collect()
    for row in status_dist:
        logger.info(f"  Status '{row['status_mahasiswa']}': {row['count']}")

    # =====================================================
    # Assignment label:
    # - Lulus (label sudah ada: 0 atau 1)
    # - Aktif → label = 1 (Terlambat)
    # =====================================================

    lulus_df = angkatan_df.filter(
        F.upper(F.trim(F.col("status_mahasiswa"))) != "AKTIF"
    )
    aktif_df = angkatan_df.filter(
        F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF"
    )

    total_lulus = lulus_df.count()
    total_aktif = aktif_df.count()
    logger.info(f"Lulus (label existing) : {total_lulus}")
    logger.info(f"Aktif (label=1)        : {total_aktif}")

    # Aktif: set label = 1 (Terlambat)
    aktif_labeled = aktif_df.withColumn("label", F.lit(1).cast(IntegerType()))

    # Gabungkan
    labeled = lulus_df.unionByName(aktif_labeled, allowMissingColumns=True)

    total_labeled = labeled.count()
    logger.info(f"Total setelah label assignment: {total_labeled}")

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
    ip_null_ids = [
        row.id_mahasiswa
        for row in labeled.filter(F.col("ip").isNull())
        .select("id_mahasiswa")
        .collect()
    ]

    logger.info("TRAINING DATA AUDIT")
    logger.info(f"Training sebelum filtering : {total_sebelum_ip_filter}")
    logger.info(f"IP NULL                    : {ip_null}")

    # =====================================================
    # Dataset final: exclude record yang fitur wajib NULL
    # (termasuk IP NULL)
    # =====================================================

    valid = labeled.dropna(subset=FEATURE_X)

    total_sesudah_filter = valid.count()
    logger.info(f"Training setelah filtering : {total_sesudah_filter}")
    logger.info(f"Selisih (dikeluarkan)      : {total_sebelum_ip_filter - total_sesudah_filter}")

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
        training_df.writeTo(table("feature_store", "training_dataset"))
        .using("iceberg")
        .createOrReplace()
    )

    final_count = training_df.count()
    logger.info(f"Rows Training Dataset : {final_count}")
    logger.info("Training Dataset berhasil dibuat.")
    logger.info("=" * 60)

    # =====================================================
    # Distribusi per angkatan
    # =====================================================

    angkatan_dist = training_df.groupBy("angkatan").count().orderBy("angkatan").collect()
    for row in angkatan_dist:
        logger.info(f"  Angkatan {row['angkatan']}: {row['count']}")

    report = {
        "table": table("feature_store", "training_dataset"),
        "jumlah_awal_angkatan_2012_2021": total_angkatan,
        "jumlah_lulus": total_lulus,
        "jumlah_aktif_dilabeli_1": total_aktif,
        "jumlah_ip_null_dikeluarkan": ip_null,
        "ip_null_ids": ip_null_ids,
        "jumlah_valid": final_count,
        "label_0_tepat_waktu": tepat_waktu,
        "label_1_terlambat": terlambat,
        "null_feature_after_dropna": 0,
        "duplicate_id": final_count
        - training_df.select("id_mahasiswa").distinct().count(),
        "leakage_forbidden": forbidden,
        "leakage_extra": extra,
        "feature_columns": FEATURE_X,
        "angkatan_distribution": {
            str(row["angkatan"]): row["count"] for row in angkatan_dist
        },
    }

    return training_df, report
