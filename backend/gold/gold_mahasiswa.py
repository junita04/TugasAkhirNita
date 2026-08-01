from pyspark.sql.functions import (
    col,
    current_date,
    months_between,
    ceil,
    when,
    lit,
    upper,
    trim,
)

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_gold_mahasiswa():

    spark = get_spark("Gold Mahasiswa")

    logger.info("=" * 60)
    logger.info("MEMBUAT GOLD MAHASISWA")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Silver Layer
    # =====================================================

    df = spark.table(f"{ICEBERG_NAMESPACE}.silver.data_referensi_mahasiswa")

    logger.info(f"Rows Silver : {df.count()}")

    # =====================================================
    # Konversi Tipe Data
    # =====================================================

    df = (
        df
        .withColumn("ipk", col("ipk").cast("double"))
        .withColumn("total_sks", col("total_sks").cast("int"))
        .withColumn("jumlah_mk", col("jumlah_mk").cast("int"))
        .withColumn("tanggal_masuk", col("tanggal_masuk").cast("date"))
        .withColumn("tanggal_keluar", col("tanggal_keluar").cast("date"))
    )

    logger.info("Konversi tipe data selesai.")

    # =====================================================
    # Ambil Total SKS Kurikulum
    # =====================================================

    kurikulum = spark.table(f"{ICEBERG_NAMESPACE}.silver.data_kurikulum")

    jumlah_sks_kurikulum = (
        kurikulum
        .select("jumlah_sks_total")
        .first()[0]
    )

    logger.info(f"SKS Kurikulum : {jumlah_sks_kurikulum}")

    # =====================================================
    # Normalisasi Status Mahasiswa
    # =====================================================

    df = df.withColumn(
        "status_mahasiswa",
        trim(col("status_mahasiswa"))
    )

    logger.info(f"Rows setelah normalisasi : {df.count()}")

    # =====================================================
    # Lama Studi (bulan)
    # =====================================================

    df = df.withColumn(
        "lama_studi_bulan",
        when(
            col("tanggal_keluar").isNull(),
            ceil(
                months_between(
                    current_date(),
                    col("tanggal_masuk")
                )
            )
        ).otherwise(
            ceil(
                months_between(
                    col("tanggal_keluar"),
                    col("tanggal_masuk")
                )
            )
        )
    )

    logger.info(f"Rows setelah lama studi : {df.count()}")

    # =====================================================
    # Estimasi Semester
    # =====================================================

    df = df.withColumn(
        "estimasi_semester",
        ceil(col("lama_studi_bulan") / lit(6))
    )

    logger.info(f"Rows setelah estimasi semester : {df.count()}")

    # =====================================================
    # Persentase SKS
    # =====================================================

    df = df.withColumn(
        "persentase_sks",
        (col("total_sks") / lit(jumlah_sks_kurikulum)) * 100
    )

    logger.info(f"Rows setelah persentase SKS : {df.count()}")

    # =====================================================
    # Status Kelulusan
    # =====================================================

    df = df.withColumn(
        "status_kelulusan",
        when(
            upper(trim(col("status_mahasiswa"))) == "LULUS",
            when(
                col("estimasi_semester") <= 8,
                lit("Tepat Waktu")
            ).otherwise(
                lit("Terlambat")
            )
        ).otherwise(
            lit(None)
        )
    )

    logger.info(f"Rows setelah status kelulusan : {df.count()}")

    # =====================================================
    # Statistik
    # =====================================================

    logger.info("=" * 60)
    logger.info("DISTRIBUSI STATUS MAHASISWA")
    logger.info("=" * 60)

    df.groupBy("status_mahasiswa").count().show(truncate=False)

    logger.info("=" * 60)
    logger.info("DISTRIBUSI STATUS KELULUSAN")
    logger.info("=" * 60)

    df.groupBy("status_kelulusan").count().show(truncate=False)

    jumlah_lulus = df.filter(
        upper(trim(col("status_mahasiswa"))) == "LULUS"
    ).count()

    jumlah_aktif = df.filter(
        upper(trim(col("status_mahasiswa"))) == "AKTIF"
    ).count()

    null_semester = df.filter(
        col("estimasi_semester").isNull()
    ).count()

    logger.info(f"Mahasiswa Lulus : {jumlah_lulus}")
    logger.info(f"Mahasiswa Aktif : {jumlah_aktif}")
    logger.info(f"NULL Estimasi Semester : {null_semester}")

    # =====================================================
    # Simpan Gold
    # =====================================================

    (
        df.writeTo(f"{ICEBERG_NAMESPACE}.gold.gold_mahasiswa")
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(f"Rows Gold Tersimpan : {df.count()}")

    logger.info("✓ Gold Mahasiswa berhasil dibuat.")
    logger.info("=" * 60)

    return df
