from pyspark.sql import functions as F

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================
# Feature Store (8 fitur, sesuai baseline notebook)
#
# Sumber : Gold dim_mahasiswa (sudah wide: termasuk ip, sks dari fact_khs)
# Fitur X: jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk,
#          sks_seharusnya, selisih_sks
# Label  : label (0=Tepat Waktu, 1=Terlambat)
# ============================================================

FEATURE_X = [
    "jk_enc",
    "angkatan",
    "ip",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "sks_seharusnya",
    "selisih_sks",
]

# Fitur yang DILARANG masuk ke X (data leakage).
# Catatan: jenis_kelamin BUKAN feature — digunakan untuk membuat jk_enc.
# ipk, total_sks ADALAH feature (bukan forbidden).
FORBIDDEN_FEATURES = [
    "jenis_kelamin",
    "tanggal_masuk",
    "tanggal_keluar",
    "status_mahasiswa",
    "lama_studi",
    "status_kelulusan",
    "label",
]

DIM_TABLE = f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa"


def join_gold_dataset():
    """
    Membaca Gold dim_mahasiswa (wide schema, sudah termasuk ip + sks).

    Grain: 1 baris = 1 mahasiswa.
    Tidak perlu JOIN lagi karena dim_mahasiswa sudah memiliki semua kolom.
    """

    spark = get_spark("TugasAkhirNita - Feature Engineering")

    logger.info("=" * 60)
    logger.info("MEMBACA GOLD DIM_MAHASISWA (WIDE SCHEMA)")
    logger.info("=" * 60)

    df = spark.table(DIM_TABLE)

    total = df.count()
    distinct = df.select("id_mahasiswa").distinct().count()
    duplicate = total - distinct

    logger.info(f"Total rows  : {total}")
    logger.info(f"Distinct id : {distinct}")
    logger.info(f"Duplicate id: {duplicate}")

    if duplicate != 0:
        raise RuntimeError(
            f"Duplicate id_mahasiswa terdeteksi pada Gold ({duplicate}). "
            "Hentikan proses Feature Store."
        )

    report = {
        "join_total": total,
        "join_distinct": distinct,
        "join_duplicate": duplicate,
        "row_multiplication": duplicate,
    }

    return df, report


def derive_features(df):
    """
    Turunkan fitur tambahan dari kolom Gold:
      - jk_enc: encoding jenis_kelamin (P/PEREMPUAN=0, L/LAKI-LAKI=1)

    Kolom lain (angkatan, semester, sks_seharusnya, selisih_sks, lama_studi,
    status_kelulusan, label) sudah ada di Gold dim_mahasiswa.
    """

    df = df.withColumn(
        "jk_enc",
        F.when(
            F.upper(F.trim(F.col("jenis_kelamin"))).isin(
                "P", "PEREMPUAN", "PEREMPUAN "
            ),
            F.lit(0),
        ).when(
            F.upper(F.trim(F.col("jenis_kelamin"))).isin(
                "L", "LAKI-LAKI", "LAKI LAKI", "LAKI"
            ),
            F.lit(1),
        ),
    )

    return df


def check_leakage(df, label_columns=()):
    """
    Pemeriksaan data leakage otomatis.

    Syarat:
      - Fitur X tepat = FEATURE_X (8 fitur).
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
