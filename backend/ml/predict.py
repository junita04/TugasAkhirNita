import os
from datetime import datetime

from pyspark.ml import PipelineModel
from pyspark.ml.classification import NaiveBayesModel
from pyspark.sql.functions import col, lit

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, MODEL_DIR
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = os.path.join(MODEL_DIR, "gaussian_nb")
FEATURE_PIPELINE_PATH = os.path.join(MODEL_DIR, "feature_pipeline")


def _default_label_order() -> list[str]:
    """Fallback urutan label bila tidak tersimpan di Model Registry."""
    return ["Tepat Waktu", "Terlambat"]


def load_label_order() -> list[str]:
    """
    Memuat urutan label (indeks StringIndexer -> label) dari metadata
    registry. Fallback ke urutan statis bila metadata tidak terbaca.
    """
    metadata_path = os.path.join(MODEL_DIR, "metadata.txt")
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Label Order"):
                    raw = line.split(":", 1)[1].strip()
                    labels = [
                        item.strip().strip("'")
                        for item in raw.strip("[]").split(",")
                        if item.strip()
                    ]
                    if labels:
                        return labels
    except (OSError, ValueError):
        logger.warning("Label order tidak terbaca; memakai urutan default.")

    return _default_label_order()


def load_model():
    """
    Load model Gaussian Naive Bayes dan feature pipeline dari Model Registry.
    """

    logger.info("=" * 60)
    logger.info("LOAD MODEL")
    logger.info("=" * 60)

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model tidak ditemukan di {MODEL_PATH}. Jalankan training dulu."
        )

    model = NaiveBayesModel.load(MODEL_PATH)
    feature_pipeline = PipelineModel.load(FEATURE_PIPELINE_PATH)

    logger.info("✓ Model dan feature pipeline berhasil dimuat.")

    return model, feature_pipeline


def predict():
    """
    Melakukan prediksi terhadap inference dataset dan menyimpan hasilnya
    ke tabel Iceberg ``feature_store.prediction_result``.

    Feature pipeline (StringIndexer jenis kelamin + VectorAssembler) yang
    dipakai adalah pipeline yang di-fit pada data training, sehingga
    pemetaan indeks fitur konsisten dengan saat training.
    """

    spark = get_spark("TugasAkhirNita - Prediction")

    logger.info("=" * 60)
    logger.info("PREDICT")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Inference Dataset
    # =====================================================

    df = spark.table(
        f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset"
    )

    logger.info(f"Rows Inference Dataset : {df.count()}")

    # =====================================================
    # Load Model + Feature Pipeline
    # =====================================================

    model, feature_pipeline = load_model()

    # =====================================================
    # Transformasi Fitur (pipeline hasil training)
    # =====================================================

    feature_df = feature_pipeline.transform(df)

    logger.info(
        f"Rows Feature Dataset : {feature_df.count()}"
    )

    # =====================================================
    # Prediction
    # =====================================================

    prediction_df = model.transform(feature_df)

    logger.info(
        f"Rows Prediction : {prediction_df.count()}"
    )

    # =====================================================
    # Map indeks -> label & simpan hasil ke Iceberg
    # =====================================================

    label_order = load_label_order()

    result_df = _build_result_table(spark, prediction_df, label_order)

    (
        result_df.writeTo(
            f"{ICEBERG_NAMESPACE}.feature_store.prediction_result"
        )
        .using("iceberg")
        .createOrReplace()
    )

    logger.info(
        "✓ Hasil prediksi tersimpan ke "
        f"{ICEBERG_NAMESPACE}.feature_store.prediction_result"
    )

    logger.info("Distribusi Hasil Prediksi")

    result_df.groupBy("prediction_label").count().show(truncate=False)

    logger.info("=" * 60)
    logger.info("PREDICT SELESAI")
    logger.info("=" * 60)

    return result_df


def _build_result_table(spark, prediction_df, label_order):
    """
    Menyusun tabel hasil prediksi dengan kolom identifier (jika ada),
    fitur, label hasil, dan probabilitas tiap kelas.
    """

    from pyspark.sql.functions import udf
    from pyspark.sql.types import ArrayType, DoubleType, StringType

    label_order = list(label_order) or _default_label_order()

    def resolve_label(idx):
        try:
            return label_order[int(idx)]
        except (ValueError, TypeError, IndexError):
            return "Terlambat"

    resolve_label_udf = udf(resolve_label, StringType())

    def split_probabilities(vector):
        if vector is None:
            return []
        return [float(value) for value in vector]

    split_probs_udf = udf(split_probabilities, ArrayType(DoubleType()))

    result_cols = [
        col("jenis_kelamin"),
        col("estimasi_semester"),
        col("ipk"),
        col("total_sks"),
        col("jumlah_mk"),
        col("persentase_sks"),
        col("prediction").alias("prediction_index"),
        resolve_label_udf(col("prediction")).alias("prediction_label"),
        split_probs_udf(col("probability")).alias("probability_vector"),
        lit(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).alias("predicted_at"),
    ]

    # Identifier (mis. NIM) hanya disertakan bila benar-benar ada di data.
    # lit(None) menghasilkan tipe 'void' yang tidak bisa ditulis ke Iceberg.
    if "nim" in prediction_df.columns:
        result_cols.insert(0, col("nim"))

    result_df = prediction_df.select(*result_cols)

    return result_df
