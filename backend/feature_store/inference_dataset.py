from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    FEATURE_X,
    derive_features,
    derive_ipk_kategori,
    check_leakage,
)
from backend.gold.gold_mahasiswa import TARGET_SKS, SNAPSHOT_SEMESTER

logger = get_logger(__name__)

# Katalog HMS-backed agar tabel terlihat oleh Trino
FE_CATALOG = "hive_iceberg"
INFERENCE_TABLE = f"{FE_CATALOG}.feature_store.inference_dataset"

# Angkatan inference
INFERENCE_ANGKATAN = [2022, 2023, 2024]


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
    logger.info("MEMBUAT INFERENCE DATASET (ANGKATAN 2022-2024, AKTIF + LULUS)")
    logger.info("=" * 60)

    df = derive_features(joined)
    df = derive_ipk_kategori(df)

    # =====================================================
    # Filter: angkatan 2022-2024 (aktif + lulus)
    # =====================================================

    angkatan_df = df.filter(F.col("angkatan").isin(INFERENCE_ANGKATAN))

    total_angkatan = angkatan_df.count()
    logger.info(f"Jumlah angkatan 2022-2024 : {total_angkatan}")

    # =====================================================
    # Distribusi per angkatan + status
    # =====================================================

    dist = angkatan_df.groupBy("angkatan", "status_mahasiswa").count().orderBy("angkatan", "status_mahasiswa").collect()
    for row in dist:
        logger.info(f"  Angkatan {row['angkatan']} | {row['status_mahasiswa']}: {row['count']}")

    # =====================================================
    # Pisahkan aktif vs lulus
    # =====================================================

    aktif_df = angkatan_df.filter(
        F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF"
    )
    lulus_df = angkatan_df.filter(
        F.upper(F.trim(F.col("status_mahasiswa"))) != "AKTIF"
    )

    total_aktif = aktif_df.count()
    total_lulus = lulus_df.count()
    logger.info(f"Aktif (snapshot 2026) : {total_aktif}")
    logger.info(f"Lulus (data existing)  : {total_lulus}")

    # =====================================================
    # Aktif: terapkan SNAPSHOT 2026
    # =====================================================

    semester_when = F.lit(None).cast(IntegerType())
    for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
        semester_when = F.when(F.col("angkatan") == angkatan, sem).otherwise(semester_when)

    aktif_df = aktif_df.withColumn("semester", semester_when)
    aktif_df = aktif_df.withColumn("sks_seharusnya", _build_snapshot_target_sks_case())
    aktif_df = aktif_df.withColumn(
        "selisih_sks",
        F.col("total_sks") - F.col("sks_seharusnya"),
    )

    # =====================================================
    # Lulus: pastikan semester, sks_seharusnya, selisih_sks ada
    # (sudah ada dari Gold, tapi pastikan tidak NULL)
    # =====================================================

    # Hitung semester lulus dari jumlah_data_khs (sudah ada di Gold)
    # semester = jumlah_data_khs (sudah benar dari Gold)
    # sks_seharusnya: map dari semester menggunakan TARGET_SKS
    lulus_sks_case = F.lit(None).cast(IntegerType())
    for sem, sks in sorted(TARGET_SKS.items()):
        lulus_sks_case = F.when(F.col("semester") == sem, sks).otherwise(lulus_sks_case)

    lulus_df = lulus_df.withColumn(
        "sks_seharusnya",
        F.coalesce(F.col("sks_seharusnya"), lulus_sks_case),
    )
    lulus_df = lulus_df.withColumn(
        "selisih_sks",
        F.when(
            F.col("selisih_sks").isNotNull(),
            F.col("selisih_sks"),
        ).otherwise(
            F.col("total_sks") - F.col("sks_seharusnya")
        ),
    )

    # =====================================================
    # Gabungkan aktif + lulus
    # =====================================================

    combined = aktif_df.unionByName(lulus_df, allowMissingColumns=True)

    total_combined = combined.count()
    logger.info(f"Gabungan aktif + lulus : {total_combined}")

    # =====================================================
    # Distribusi label (lulus punya label 0/1, aktif punya label NULL)
    # =====================================================

    label_dist = combined.groupBy("label").count().collect()
    for row in label_dist:
        label_name = "NULL (aktif)" if row["label"] is None else str(row["label"])
        logger.info(f"  Label {label_name}: {row['count']}")

    # =====================================================
    # Filter: IP TIDAK NULL
    # =====================================================

    total_sebelum_ip_filter = combined.count()
    ip_null = combined.filter(F.col("ip").isNull()).count()
    ip_null_ids = [
        row.id_mahasiswa
        for row in combined.filter(F.col("ip").isNull())
        .select("id_mahasiswa")
        .collect()
    ]

    logger.info("INFERENCE DATA AUDIT")
    logger.info(f"Inference sebelum filtering IP : {total_sebelum_ip_filter}")
    logger.info(f"IP NULL                        : {ip_null}")

    combined = combined.filter(F.col("ip").isNotNull())

    total_sesudah_ip_filter = combined.count()
    logger.info(f"Inference setelah filtering IP  : {total_sesudah_ip_filter}")
    logger.info(f"Selisih (dikeluarkan)          : {total_sebelum_ip_filter - total_sesudah_ip_filter}")

    # =====================================================
    # Reconciliation check SEBELUM dropna
    # =====================================================

    total_sebelum_dropna = combined.count()
    logger.info(f"Reconciliation SEBELUM dropna: {total_sebelum_dropna}")

    # =====================================================
    # Dataset final: pastikan tidak ada NULL pada fitur wajib
    # =====================================================

    valid = combined.dropna(subset=FEATURE_X)

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
    logger.info(f"Selisih: {jumlah_hilang}")

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

    final_count = inference_df.count()
    logger.info(f"Rows Inference Dataset : {final_count}")
    logger.info("Inference Dataset berhasil dibuat.")
    logger.info("=" * 60)

    # =====================================================
    # Reconciliation per angkatan
    # =====================================================

    for angkatan in INFERENCE_ANGKATAN:
        cnt = inference_df.filter(F.col("angkatan") == angkatan).count()
        logger.info(f"  Angkatan {angkatan}: {cnt}")

    # =====================================================
    # Distribusi angkatan
    # =====================================================

    angkatan_dist = inference_df.groupBy("angkatan").count().orderBy("angkatan").collect()
    for row in angkatan_dist:
        logger.info(f"  Angkatan {row['angkatan']}: {row['count']}")

    report = {
        "table": INFERENCE_TABLE,
        "jumlah_awal_angkatan_2022_2024": total_angkatan,
        "jumlah_aktif": total_aktif,
        "jumlah_lulus": total_lulus,
        "jumlah_ip_null_dikeluarkan": ip_null,
        "ip_null_ids": ip_null_ids,
        "jumlah_valid": final_count,
        "jumlah_sebelum_dropna": total_sebelum_dropna,
        "jumlah_sesudah_dropna": total_sesudah_dropna,
        "jumlah_hilang_dropna": jumlah_hilang,
        "null_feature_after_dropna": 0,
        "duplicate_id": final_count
        - inference_df.select("id_mahasiswa").distinct().count(),
        "leakage_forbidden": forbidden,
        "leakage_extra": extra,
        "feature_columns": FEATURE_X,
        "angkatan_distribution": {
            str(row["angkatan"]): row["count"] for row in angkatan_dist
        },
    }

    return inference_df, report
