from pyspark.ml import Pipeline
from pyspark.ml.classification import NaiveBayesModel
from pyspark.ml.feature import StringIndexer, VectorAssembler

from backend.spark.session import get_spark
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = "models/gaussian_nb"


def load_model():
    """
    Load model Gaussian Naive Bayes dari Model Registry.
    """

    logger.info("=" * 60)
    logger.info("LOAD MODEL")
    logger.info("=" * 60)

    model = NaiveBayesModel.load(MODEL_PATH)

    logger.info("✓ Model berhasil dimuat.")

    return model


def predict():
    """
    Melakukan prediksi terhadap inference dataset.
    """

    spark = get_spark("Prediction")

    logger.info("=" * 60)
    logger.info("PREDICT")
    logger.info("=" * 60)

    # =====================================================
    # Membaca Inference Dataset
    # =====================================================

    df = spark.table(
        "local.feature_store.inference_dataset"
    )

    logger.info(f"Rows Inference Dataset : {df.count()}")

    # =====================================================
    # String Indexer
    # =====================================================

    gender_indexer = StringIndexer(
        inputCol="jenis_kelamin",
        outputCol="jenis_kelamin_index",
        handleInvalid="keep"
    )

    # =====================================================
    # Vector Assembler
    # =====================================================

    assembler = VectorAssembler(
        inputCols=[
            "jenis_kelamin_index",
            "estimasi_semester",
            "ipk",
            "total_sks",
            "jumlah_mk",
            "persentase_sks"
        ],
        outputCol="features"
    )

    pipeline = Pipeline(
        stages=[
            gender_indexer,
            assembler
        ]
    )

    pipeline_model = pipeline.fit(df)

    feature_df = pipeline_model.transform(df)

    logger.info(
        f"Rows Feature Dataset : {feature_df.count()}"
    )

    # =====================================================
    # Load Model
    # =====================================================

    model = load_model()

    # =====================================================
    # Prediction
    # =====================================================

    prediction_df = model.transform(feature_df)

    logger.info(
        f"Rows Prediction : {prediction_df.count()}"
    )

    logger.info("=" * 60)
    logger.info("PREDICT SELESAI")
    logger.info("=" * 60)

    return prediction_df