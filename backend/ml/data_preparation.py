import numpy as np

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

TRAINING_TABLE = f"{ICEBERG_NAMESPACE}.feature_store.training_dataset"

TARGET_COLUMN = "label"
IDENTIFIER_COLUMN = "id_mahasiswa"

FEATURE_COLUMNS = [
    "jk_enc",
    "angkatan",
    "ip",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "sks_seharusnya",
    "selisih_sks",
]

FORBIDDEN_FEATURES = [
    IDENTIFIER_COLUMN,  # hanya identifier, bukan X
    "lama_studi",
    "tanggal_keluar",
    "status_mahasiswa",
    "status_kelulusan",
    "jenis_kelamin",
    "tanggal_masuk",
]

POSITIVE_CLASS = 1  # Terlambat (label=1)


def load_training_dataset():
    """
    Membaca training dataset dari Feature Store dan mengembalikannya
    sebagai pandas DataFrame.

    Training dataset sudah bersih: tidak ada null pada fitur wajib,
    tidak ada duplicate id (grain 1 baris = 1 mahasiswa dengan label).
    """

    spark = get_spark("TugasAkhirNita - ML Data Preparation")

    logger.info("=" * 60)
    logger.info("MEMUAT TRAINING DATASET (FEATURE STORE)")
    logger.info("=" * 60)

    df = spark.table(TRAINING_TABLE)

    pdf = df.toPandas()

    logger.info(f"Rows         : {len(pdf)}")
    logger.info(f"Kolom        : {list(pdf.columns)}")

    _validate_dataset(pdf)

    return pdf


def _validate_dataset(pdf):
    """Validasi dataset sebelum modeling: schema, null, duplicate, distribusi."""

    expected = set(FEATURE_COLUMNS) | {TARGET_COLUMN, IDENTIFIER_COLUMN}
    extra = [column for column in pdf.columns if column not in expected]
    if extra:
        raise RuntimeError(f"Kolom di luar schema training dataset: {extra}")

    missing = [c for c in expected if c not in pdf.columns]
    if missing:
        raise RuntimeError(f"Kolom yang dibutuhkan tidak ditemukan: {missing}")

    null_features = {
        column: int(pdf[column].isnull().sum())
        for column in FEATURE_COLUMNS
    }
    null_target = int(pdf[TARGET_COLUMN].isnull().sum())

    duplicate_id = int(pdf[IDENTIFIER_COLUMN].duplicated().sum())
    total = len(pdf)
    distinct_id = int(pdf[IDENTIFIER_COLUMN].nunique())

    class_dist = pdf[TARGET_COLUMN].value_counts().to_dict()

    logger.info(f"Distinct id             : {distinct_id}")
    logger.info(f"Duplicate id            : {duplicate_id}")
    logger.info(f"Null fitur              : {null_features}")
    logger.info(f"Null target             : {null_target}")
    logger.info(f"Grain 1 baris = 1 mhs   : {'PASS' if total == distinct_id else 'FAIL'}")
    logger.info(f"Distribusi target       : {class_dist}")

    if duplicate_id != 0:
        raise RuntimeError(f"Duplicate id_mahasiswa ditemukan: {duplicate_id}")

    null_values = {k: v for k, v in null_features.items() if v}
    if null_values:
        logger.warning(f"Nilai null pada fitur wajib (tidak diimputasi): {null_values}")

    if null_target:
        logger.warning(f"Nilai null pada target: {null_target}")


def check_model_leakage(pdf):
    """
    Pemeriksaan leakage otomatis sebelum training.

    Hanya X = [jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk,
               sks_seharusnya, selisih_sks] yang boleh masuk input model.
    Y = label (0/1), id_mahasiswa = identifier.
    """

    allowed = set(FEATURE_COLUMNS) | {TARGET_COLUMN, IDENTIFIER_COLUMN}

    unexpected = [c for c in pdf.columns if c not in allowed]
    if unexpected:
        raise RuntimeError(
            "DATA LEAKAGE DETECTED: "
            f"kolom di luar X/Y terdeteksi: {unexpected}. "
            "Training dihentikan."
        )

    return []


def build_target_encoding(pdf):
    """
    Enkoding target integer -> integer (sudah 0/1).

    Mapping:
      - 0 -> 0 (Tepat Waktu)
      - 1 -> 1 (Terlambat)

    Dictionary mapping disimpan agar konsisten saat inferensi.
    """

    classes = sorted(pdf[TARGET_COLUMN].unique().tolist())
    mapping = {label: index for index, label in enumerate(classes)}

    logger.info(f"Class mapping : {mapping}")

    return mapping


def encode_target(pdf, mapping):
    y = pdf[TARGET_COLUMN].map(mapping).astype(int)
    return y


def numpy_X(pdf):
    X = pdf[FEATURE_COLUMNS].astype(float).to_numpy()
    return X
