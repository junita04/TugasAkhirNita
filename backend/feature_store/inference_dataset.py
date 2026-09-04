from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    FEATURE_X,
    derive_features,
    check_leakage,
)
from backend.gold.gold_mahasiswa import TARGET_SKS, SNAPSHOT_SEMESTER

logger = get_logger(__name__)

INFERENCE_TABLE = f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset"
INFERENCE_TABLE_HIVE = "hive_iceberg.feature_store.inference_dataset"


def _build_snapshot_target_sks_case():
    """Membangun CASE expression untuk snapshot sks_seharusnya per angkatan."""
    when_expr = F.lit(None).cast(IntegerType())
    for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
        sks = TARGET_SKS[sem]
        when_expr = F.when(F.col("angkatan") == angkatan, sks).otherwise(when_expr)
    return when_expr


def create_inference_dataset(joined):

    spark = joined.sparkSession

    logger.info("=" * 60)
    logger.info("MEMBUAT INFERENCE DATASET (AKTIF 2022-2024, SNAPSHOT 2026)")
    logger.info("=" * 60)

    df = derive_features(joined)

    # =====================================================
    # Filter mahasiswa AKTIF angkatan 2022, 2023, 2024
    # =====================================================

    aktif = df.filter(
        (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF")
        & (F.col("angkatan").isin(2022, 2023, 2024))
    )

    total_aktif = aktif.count()
    logger.info(f"Jumlah awal mahasiswa AKTIF 2022-2024 : {total_aktif}")

    # =====================================================
    # Distribusi per angkatan
    # =====================================================

    angkatan_dist = aktif.groupBy("angkatan").count().collect()
    for row in angkatan_dist:
        logger.info(f"  Angkatan {row['angkatan']}: {row['count']}")

    # =====================================================
    # Terapkan SNAPSHOT 2026:
    # - semester_snapshot per angkatan
    # - sks_seharusnya_snapshot dari TARGET_SKS
    # - selisih_sks_snapshot = total_sks - sks_seharusnya_snapshot
    # =====================================================

    # Map angkatan -> snapshot semester
    semester_when = F.lit(None).cast(IntegerType())
    for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
        semester_when = F.when(F.col("angkatan") == angkatan, sem).otherwise(semester_when)

    aktif = aktif.withColumn("semester", semester_when)

    # Map angkatan -> snapshot target SKS
    aktif = aktif.withColumn("sks_seharusnya", _build_snapshot_target_sks_case())

    # selisih_sks = total_sks - sks_seharusnya (snapshot)
    aktif = aktif.withColumn(
        "selisih_sks",
        F.col("total_sks") - F.col("sks_seharusnya"),
    )

    # =====================================================
    # Mahasiswa AKTIF dengan IP NULL harus DIKELUARKAN
    # TIDAK ada imputasi - IP NULL = tidak digunakan untuk ML
    # =====================================================

    total_sebelum_ip_filter = aktif.count()
    ip_null = aktif.filter(F.col("ip").isNull()).count()
    ip_null_ids = [row.id_mahasiswa for row in aktif.filter(F.col("ip").isNull()).select("id_mahasiswa").collect()]
    logger.info(f"INFERENCE DATA AUDIT")
    logger.info(f"Inference sebelum filtering IP : {total_sebelum_ip_filter}")
    logger.info(f"IP NULL                        : {ip_null}")

    # Filter: HANYA mahasiswa dengan IP TIDAK NULL
    aktif = aktif.filter(F.col("ip").isNotNull())

    total_sesudah_ip_filter = aktif.count()
    logger.info(f"Inference setelah filtering IP  : {total_sesudah_ip_filter}")
    logger.info(f"Selisih (dikeluarkan)          : {total_sebelum_ip_filter - total_sesudah_ip_filter}")

    # =====================================================
    # Reconciliation check SEBELUM dropna
    # =====================================================

    total_sebelum_dropna = aktif.count()
    logger.info(f"Reconciliation SEBELUM dropna: {total_sebelum_dropna}")

    # =====================================================
    # Dataset final: pastikan tidak ada NULL pada fitur wajib
    # =====================================================

    valid = aktif.dropna(subset=FEATURE_X)

    total_sesudah_dropna = valid.count()
    jumlah_hilang = total_sebelum_dropna - total_sesudah_dropna

    if jumlah_hilang > 0:
        logger.warning(
            f"PERINGATAN: {jumlah_hilang} baris hilang setelah dropna! "
            "Memeriksa kolom NULL..."
        )
        for col_name in FEATURE_X:
            null_count = valid.filter(F.col(col_name).isNull()).count()
            if null_count > 0:
                logger.warning(f"  {col_name}: {null_count} NULL")

    logger.info(f"Reconciliation SESUDAH dropna: {total_sesudah_dropna}")
    logger.info(f"Selisih: {jumlah_hilang} (harusnya 0)")

    valid = valid.dropDuplicates(["id_mahasiswa"])

    inference_df = valid.select("id_mahasiswa", *FEATURE_X)

    # =====================================================
    # Reconciliation: pastikan semua angkatan terpelihara
    # =====================================================

    for angkatan, expected_count in [
        (2022, 4109), (2023, 4046), (2024, 4346)
    ]:
        actual_count = inference_df.filter(F.col("angkatan") == angkatan).count()
        if actual_count != expected_count:
            logger.warning(
                f"REKONCILIASI: Angkatan {angkatan} "
                f"expected={expected_count} actual={actual_count} "
                f"delta={actual_count - expected_count}"
            )
        else:
            logger.info(f"Rekonciliasi angkatan {angkatan}: {actual_count} OK")

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

    # Write to HMS-backed catalog for Trino visibility
    (
        inference_df.writeTo(INFERENCE_TABLE_HIVE)
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(f"Rows Inference Dataset : {inference_df.count()}")
    logger.info("✓ Inference Dataset berhasil dibuat.")
    logger.info("=" * 60)

    # =====================================================
    # Validasi snapshot
    # =====================================================

    logger.info("SNAPSHOT 2026 VALIDATION:")
    for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
        sks = TARGET_SKS[sem]
        logger.info(f"  Angkatan {angkatan} -> semester {sem} -> {sks} SKS")

    # =====================================================
    # Validasi sks_seharusnya pada inference dataset
    # =====================================================

    logger.info("=" * 60)
    logger.info("VALIDASI INFERENCE DATASET - SKS_SEHARUSNYA")
    logger.info("=" * 60)

    # Validasi: tidak boleh ada sks_seharusnya > 144
    invalid_sks = inference_df.filter(
        (F.col("sks_seharusnya").isNull())
        | (F.col("sks_seharusnya") < 15)
        | (F.col("sks_seharusnya") > 144)
    ).count()

    if invalid_sks > 0:
        logger.warning(f"VALIDASI GAGAL: {invalid_sks} baris memiliki sks_seharusnya di luar rentang 15-144!")
        invalid_samples = inference_df.filter(
            (F.col("sks_seharusnya").isNull())
            | (F.col("sks_seharusnya") < 15)
            | (F.col("sks_seharusnya") > 144)
        ).select("id_mahasiswa", "angkatan", "sks_seharusnya", "total_sks").limit(5)
        invalid_samples.show()
        raise RuntimeError(f"Inference dataset memiliki sks_seharusnya di luar rentang 15-144: {invalid_sks} baris")
    else:
        logger.info("✓ sks_seharusnya valid (15-144)")

    # Validasi per angkatan
    for angkatan, expected_sks in [
        (2022, 135), (2023, 95), (2024, 55)
    ]:
        actual_sks = inference_df.filter(
            F.col("angkatan") == angkatan
        ).select("sks_seharusnya").first()[0]
        if actual_sks != expected_sks:
            raise RuntimeError(
                f"Angkatan {angkatan}: sks_seharusnya={actual_sks}, "
                f"expected={expected_sks}"
            )
        logger.info(f"✓ Angkatan {angkatan}: sks_seharusnya={actual_sks}")

    report = {
        "table": INFERENCE_TABLE,
        "jumlah_awal_aktif_2022_2024": total_aktif,
        "jumlah_ip_null_dikeluarkan": ip_null,
        "ip_null_ids": ip_null_ids,
        "jumlah_valid": inference_df.count(),
        "jumlah_sebelum_dropna": total_sebelum_dropna,
        "jumlah_sesudah_dropna": total_sesudah_dropna,
        "jumlah_hilang_dropna": jumlah_hilang,
        "null_feature_after_dropna": 0,
        "duplicate_id": inference_df.count()
        - inference_df.select("id_mahasiswa").distinct().count(),
        "leakage_forbidden": forbidden,
        "leakage_extra": extra,
        "snapshot_semester": SNAPSHOT_SEMESTER,
        "snapshot_target_sks": {k: TARGET_SKS[v] for k, v in SNAPSHOT_SEMESTER.items()},
        "feature_columns": FEATURE_X,
        "rekonciliasi": {
            a: inference_df.filter(F.col("angkatan") == a).count()
            for a in [2022, 2023, 2024]
        },
    }

    return inference_df, report
