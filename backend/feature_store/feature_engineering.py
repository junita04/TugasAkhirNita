from pyspark.sql import functions as F

from backend.spark.session import get_spark
from backend.config.settings import (
    ICEBERG_NAMESPACE,
    GRADUATION_LIMIT_DAYS,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================
# Feature Store baru (Tahap 4)
#
# Sumber : Gold Star Schema (dim_mahasiswa + fact_khs)
# Fitur X: ip, sks, angkatan, jumlah_mk
# Label  : status_kelulusan (hanya untuk mahasiswa LULUS)
# ============================================================

FEATURE_X = ["ip", "sks", "angkatan", "jumlah_mk"]

# Fitur yang DILARANG masuk ke X (data leakage).
FORBIDDEN_FEATURES = [
    "jenis_kelamin",
    "tanggal_masuk",
    "tanggal_keluar",
    "ipk",
    "total_sks",
    "status_mahasiswa",
    "lama_studi",
    "status_kelulusan",
    "estimasi_semester",
    "persentase_sks",
]

DIM_TABLE = f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa"
FACT_TABLE = f"{ICEBERG_NAMESPACE}.gold.fact_khs"


def join_gold_dataset():
    """
    Membaca Gold Star Schema dan melakukan LEFT JOIN:

        gold.dim_mahasiswa
        LEFT JOIN gold.fact_khs
        ON id_mahasiswa

    Grain hasil join: 1 baris = 1 mahasiswa.
    """

    spark = get_spark("TugasAkhirNita - Feature Engineering")

    logger.info("=" * 60)
    logger.info("JOIN GOLD STAR SCHEMA (dim_mahasiswa + fact_khs)")
    logger.info("=" * 60)

    dim = spark.table(DIM_TABLE)
    fact = spark.table(FACT_TABLE)

    joined = dim.join(fact, on="id_mahasiswa", how="left")

    total = joined.count()
    distinct = joined.select("id_mahasiswa").distinct().count()
    duplicate = total - distinct
    row_multiplication = duplicate

    logger.info(f"Join total rows : {total}")
    logger.info(f"Distinct id     : {distinct}")
    logger.info(f"Duplicate id    : {duplicate}")

    if row_multiplication != 0:
        raise RuntimeError(
            f"Row multiplication terdeteksi pada JOIN Gold ({row_multiplication}). "
            "Hentikan proses Feature Store."
        )

    report = {
        "join_total": total,
        "join_distinct": distinct,
        "join_duplicate": duplicate,
        "row_multiplication": row_multiplication,
    }

    return joined, report


def derive_features(joined):
    """
    Turunkan fitur baru dari kolom dasar Gold:
      - angkatan = year(tanggal_masuk)   (hanya dari tanggal MASUK)
      - lama_studi = tanggal_keluar - tanggal_masuk (dalam HARI)
        Hanya dipakai untuk membentuk label training; bukan fitur X.
    """

    df = joined.withColumn("angkatan", F.year(F.col("tanggal_masuk")))

    df = df.withColumn(
        "lama_studi",
        F.datediff(F.col("tanggal_keluar"), F.col("tanggal_masuk")),
    )

    return df


def check_leakage(df, label_columns=()):
    """
    Pemeriksaan data leakage otomatis.

    Syarat:
      - Fitur X tepat = FEATURE_X (ip, sks, angkatan, jumlah_mk).
      - Tidak ada fitur terlarang di dalam dataset (selain id/label).

    Mengembalikan (forbidden_detected, extra_columns).
    """

    forbidden_detected = [
        column
        for column in FORBIDDEN_FEATURES
        if column in df.columns and column not in label_columns
    ]

    x_set = set(FEATURE_X)
    allowed = x_set | set(label_columns) | {"id_mahasiswa"}
    extra_columns = [c for c in df.columns if c not in allowed]

    if forbidden_detected or extra_columns:
        raise RuntimeError(
            "DATA LEAKAGE DETECTED: "
            f"forbidden={forbidden_detected} extra={extra_columns}. "
            "Hentikan proses sebelum Feature Store ditulis."
        )

    return forbidden_detected, extra_columns
