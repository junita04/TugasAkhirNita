"""
Tahap 2 - Jembatan (interface) Feature Store Iceberg -> dataset siap-ML.

Tujuan
------
Menyediakan ANTARMUKA BACA-SAJA yang menyiapkan data ML langsung dari
Feature Store Iceberg:

    hive_iceberg.feature_store.training_dataset
    hive_iceberg.feature_store.inference_dataset

sehingga tahap ML berikutnya tidak lagi bergantung pada snapshot Excel
statis (``data fix/training_dataset_full.xlsx`` dsb.).

Prinsip dan batasan (Tahap 2)
-----------------------------
1. Modul ini TIDAK menulis ke tabel Gold/Feature Store yang sudah ada.
2. Aturan pembentukan fitur/label TIDAK diubah. Satu-satunya kolom turunan
   yang dibuat adalah ``angkatan_enc`` dengan aturan yang sudah terbukti ada
   pada dataset existing (lihat ``ANGKATAN_ENC_RULE``): hasilnya identik
   dengan kolom ``angkatan_enc`` pada ``training_dataset_full.xlsx``
   (2012-2015 -> 0, 2016-2018 -> 1, >=2019 -> 2).
3. Penamaan kolom diselaraskan dengan konvensi model:
   ``IPK_kategori`` (Feature Store) -> ``ipk_kategori`` (model).
4. Ekspor ke tabel ditulis dalam fungsi terpisah yang DEFAULT NONAKTIF dan
   hanya boleh menulis ke tabel terisolasi (bukan output produksi). Modul
   ini tidak dipanggil dengan ``enabled=True`` oleh DAG mana pun.

Kontrak kolom ML (hasil ``build_ml_training_frame``)::

    id_mahasiswa, jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk,
    sks_seharusnya, selisih_sks, kecepatan_sks_per_semester,
    ipk_kategori, angkatan_enc, label
"""

from backend.utils.logger import get_logger
from backend.feature_store.feature_engineering import FEATURE_X

logger = get_logger(__name__)


# ============================================================
# Tabel Feature Store (sumber, baca-saja)
# ============================================================

FS_CATALOG = "hive_iceberg"
FS_TRAINING_TABLE = f"{FS_CATALOG}.feature_store.training_dataset"
FS_INFERENCE_TABLE = f"{FS_CATALOG}.feature_store.inference_dataset"


# ============================================================
# Aturan angkatan_enc (DIREKAM dari dataset existing, TIDAK diubah)
#
# Terverifikasi dari training_dataset_full.xlsx dan inference_dataset_full.xlsx:
#   2012-2015 -> 0 ; 2016-2018 -> 1 ; 2019+ -> 2
# ============================================================

ANGKATAN_ENC_LOW_MAX = 2015
ANGKATAN_ENC_MID_MAX = 2018
ANGKATAN_ENC_RULE = (
    f"angkatan <= {ANGKATAN_ENC_LOW_MAX} -> 0 ; "
    f"{ANGKATAN_ENC_LOW_MAX + 1}-{ANGKATAN_ENC_MID_MAX} -> 1 ; "
    f">= {ANGKATAN_ENC_MID_MAX + 1} -> 2"
)


# ============================================================
# Kontrak kolom
# ============================================================

# Kolom yang WAJIB ada pada tabel Feature Store (sumber).
FS_TRAINING_COLUMNS = ["id_mahasiswa", *FEATURE_X, "label"]
FS_INFERENCE_COLUMNS = ["id_mahasiswa", *FEATURE_X]

# Penyelarasan nama kolom Feature Store -> konvensi model.
ML_RENAME_MAP = {"IPK_kategori": "ipk_kategori"}

# Kolom fitur pada dataset ML (setelah rename + angkatan_enc).
ML_FEATURE_COLUMNS = [
    ML_RENAME_MAP.get(col, col) for col in FEATURE_X
] + ["angkatan_enc"]

# Kolom lengkap dataset ML.
ML_TRAINING_COLUMNS = ["id_mahasiswa", *ML_FEATURE_COLUMNS, "label"]
ML_INFERENCE_COLUMNS = ["id_mahasiswa", *ML_FEATURE_COLUMNS]


# ============================================================
# Target ekspor terisolasi (DEV hanya, NONAKTIF secara default)
#
# Tabel ini BUKAN output produksi. Gunakan hanya untuk pengembangan/QA.
# ============================================================

ML_EXPORT_CATALOG = FS_CATALOG
ML_EXPORT_NAMESPACE = "feature_store"
ML_EXPORT_TRAINING_TABLE = f"{ML_EXPORT_CATALOG}.{ML_EXPORT_NAMESPACE}.ml_training_dataset_v1"
ML_EXPORT_INFERENCE_TABLE = f"{ML_EXPORT_CATALOG}.{ML_EXPORT_NAMESPACE}.ml_inference_dataset_v1"


# ============================================================
# Helper murni (tanpa Spark) - dapat diuji secara statis
# ============================================================

def encode_angkatan_value(angkatan):
    """Kembalikan nilai ``angkatan_enc`` untuk satu tahun angkatan.

    Mengembalikan ``None`` bila ``angkatan`` None (konsisten dengan perilaku
    kolom Spark yang mengembalikan NULL).
    """
    if angkatan is None:
        return None
    if angkatan <= ANGKATAN_ENC_LOW_MAX:
        return 0
    if angkatan <= ANGKATAN_ENC_MID_MAX:
        return 1
    return 2


def expected_ml_training_columns():
    return list(ML_TRAINING_COLUMNS)


def expected_ml_inference_columns():
    return list(ML_INFERENCE_COLUMNS)


# ============================================================
# Transformasi Spark (spark diimpor lazily)
# ============================================================

def _angkatan_enc_expr(col_name="angkatan"):
    from pyspark.sql import functions as F
    from pyspark.sql.types import IntegerType

    col = F.col(col_name)
    return (
        F.when(col.isNull(), F.lit(None).cast(IntegerType()))
        .when(col <= ANGKATAN_ENC_LOW_MAX, F.lit(0))
        .when(col <= ANGKATAN_ENC_MID_MAX, F.lit(1))
        .otherwise(F.lit(2))
        .cast(IntegerType())
    )


def _require_columns(df, required, label):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Tabel Feature Store ({label}) tidak memiliki kolom wajib: {missing}. "
            f"Kolom tersedia: {df.columns}"
        )


def _to_ml_frame(fs_df, source_columns, ml_columns, label):
    _require_columns(fs_df, source_columns, label)

    df = fs_df.withColumn("angkatan_enc", _angkatan_enc_expr("angkatan"))

    for old_name, new_name in ML_RENAME_MAP.items():
        if old_name in df.columns:
            df = df.withColumnRenamed(old_name, new_name)

    return df.select(*ml_columns)


def build_ml_training_frame(fs_df):
    """Feature Store training -> kerangka dataset ML (baca-saja, in-memory)."""
    return _to_ml_frame(
        fs_df, FS_TRAINING_COLUMNS, ML_TRAINING_COLUMNS, "training"
    )


def build_ml_inference_frame(fs_df):
    """Feature Store inference -> kerangka dataset ML (baca-saja, in-memory)."""
    return _to_ml_frame(
        fs_df, FS_INFERENCE_COLUMNS, ML_INFERENCE_COLUMNS, "inference"
    )


# ============================================================
# Validasi (baca-saja)
# ============================================================

def _null_feature_report(df):
    from pyspark.sql import functions as F

    report = {}
    for col in ML_FEATURE_COLUMNS:
        null_count = df.filter(F.col(col).isNull()).count()
        if null_count:
            report[col] = null_count
    return report


def validate_ml_frame(df, expect_label):
    """Validasi kerangka ML: kolom, jumlah baris, duplikasi, NULL, label."""
    from pyspark.sql import functions as F

    expected = ML_TRAINING_COLUMNS if expect_label else ML_INFERENCE_COLUMNS
    missing = [col for col in expected if col not in df.columns]

    rows = df.count()
    distinct_id = df.select("id_mahasiswa").distinct().count()

    report = {
        "columns": list(df.columns),
        "expected_columns": list(expected),
        "missing_columns": missing,
        "rows": rows,
        "distinct_id": distinct_id,
        "duplicate_id": rows - distinct_id,
        "null_features": _null_feature_report(df),
    }

    if expect_label:
        label_dist = {}
        for row in df.groupBy("label").count().collect():
            label_dist[str(row["label"])] = row["count"]
        report["label_distribution"] = label_dist

    return report


def load_feature_store_frames(spark=None):
    """Baca tabel Feature Store (baca-saja). Spark diimpor lazily."""
    if spark is None:
        from backend.spark.session import get_spark

        spark = get_spark("Tahap 2 - ML Export")

    training_fs = spark.table(FS_TRAINING_TABLE)
    inference_fs = spark.table(FS_INFERENCE_TABLE)
    return training_fs, inference_fs


def validate_feature_store_datasets(spark=None):
    """Validasi lengkap dataset ML yang berasal dari Feature Store.

    BACA-SAJA: tidak menulis tabel apa pun. Mengembalikan dict laporan.
    """
    training_fs, inference_fs = load_feature_store_frames(spark)

    ml_training = build_ml_training_frame(training_fs)
    ml_inference = build_ml_inference_frame(inference_fs)

    report = {
        "source_tables": {
            "training": FS_TRAINING_TABLE,
            "inference": FS_INFERENCE_TABLE,
        },
        "angkatan_enc_rule": ANGKATAN_ENC_RULE,
        "rename_map": ML_RENAME_MAP,
        "training": validate_ml_frame(ml_training, expect_label=True),
        "inference": validate_ml_frame(ml_inference, expect_label=False),
    }

    logger.info("=" * 60)
    logger.info("VALIDASI FEATURE STORE -> ML (Tahap 2, baca-saja)")
    logger.info(f"  training rows  : {report['training']['rows']}")
    logger.info(f"  inference rows : {report['inference']['rows']}")
    logger.info(f"  angkatan_enc   : {ANGKATAN_ENC_RULE}")
    logger.info("=" * 60)

    return report


# ============================================================
# Ekspor OPSIONAL ke tabel terisolasi (NONAKTIF secara default)
# ============================================================

def export_ml_datasets(enabled=False, spark=None):
    """Ekspor dataset ML ke tabel terisolasi (DEV).

    DEFAULT NONAKTIF. Fungsi ini hanya menulis bila dipanggil dengan
    ``enabled=True`` secara eksplisit, dan hanya ke tabel terisolasi
    ``ml_training_dataset_v1`` / ``ml_inference_dataset_v1`` (bukan output
    produksi). Tidak dipanggil oleh DAG mana pun pada Tahap 2.
    """
    if not enabled:
        logger.warning(
            "export_ml_datasets: NONAKTIF (default). Tidak ada tabel yang ditulis."
        )
        return None

    ml_training = build_ml_training_frame(load_feature_store_frames(spark)[0])
    ml_inference = build_ml_inference_frame(load_feature_store_frames(spark)[1])

    logger.warning(
        "export_ml_datasets AKTIF: menulis ke tabel terisolasi (DEV): "
        f"{ML_EXPORT_TRAINING_TABLE}, {ML_EXPORT_INFERENCE_TABLE}"
    )

    (
        ml_training.writeTo(ML_EXPORT_TRAINING_TABLE)
        .using("iceberg")
        .createOrReplace()
    )
    (
        ml_inference.writeTo(ML_EXPORT_INFERENCE_TABLE)
        .using("iceberg")
        .createOrReplace()
    )

    return {
        "training": ML_EXPORT_TRAINING_TABLE,
        "inference": ML_EXPORT_INFERENCE_TABLE,
    }
