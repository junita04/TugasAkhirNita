from pyspark.ml.classification import NaiveBayes
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

from backend.ml.data_preparation import prepare_training_dataset
from backend.spark.session import get_spark
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def train_model():

    # =====================================================
    # Spark Session
    # =====================================================

    spark = get_spark("Train Model")

    logger.info("=" * 60)
    logger.info("TRAINING GAUSSIAN NAIVE BAYES")
    logger.info("=" * 60)

    # =====================================================
    # Data Preparation
    # =====================================================

    prepared_df = prepare_training_dataset()

    prepared_df.cache()

    total_rows = prepared_df.count()

    logger.info(f"Rows Prepared Dataset : {total_rows}")

    # =====================================================
    # Train Test Split
    # =====================================================

    train_df, test_df = prepared_df.randomSplit(
        [0.8, 0.2],
        seed=42
    )

    train_count = train_df.count()
    test_count = test_df.count()

    logger.info(f"Rows Training : {train_count}")
    logger.info(f"Rows Testing  : {test_count}")

    # =====================================================
    # Gaussian Naive Bayes
    # =====================================================

    nb = NaiveBayes(
        featuresCol="features",
        labelCol="label",
        predictionCol="prediction",
        probabilityCol="probability",
        rawPredictionCol="rawPrediction",
        modelType="gaussian"
    )

    # =====================================================
    # Parameter Grid
    # =====================================================

    param_grid = (
        ParamGridBuilder()
        .addGrid(
            nb.smoothing,
            [0.1, 0.5, 1.0]
        )
        .build()
    )

    logger.info(f"Jumlah kombinasi parameter : {len(param_grid)}")

    # =====================================================
    # Evaluator
    # =====================================================

    evaluator = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    )

    # =====================================================
    # Cross Validation
    # =====================================================

    cross_validator = CrossValidator(
        estimator=nb,
        estimatorParamMaps=param_grid,
        evaluator=evaluator,
        numFolds=10,
        seed=42
    )

    logger.info("Training Gaussian Naive Bayes...")

    cv_model = cross_validator.fit(train_df)

    logger.info("Training selesai.")

    # =====================================================
    # Best Model
    # =====================================================

    best_model = cv_model.bestModel

    logger.info("Best Model berhasil dibuat.")
    logger.info(
        f"Best Smoothing : {best_model.getSmoothing()}"
    )

    # =====================================================
    # Prediksi Data Testing
    # =====================================================

    prediction_test = best_model.transform(test_df)

    logger.info(
        f"Rows Prediction : {prediction_test.count()}"
    )

    logger.info("=" * 60)
    logger.info("TRAINING SELESAI")
    logger.info("=" * 60)

    return {
        "spark": spark,
        "model": best_model,
        "cross_validator": cv_model,
        "prepared_df": prepared_df,
        "train_df": train_df,
        "test_df": test_df,
        "prediction_test": prediction_test,
        "train_count": train_count,
        "test_count": test_count,
        "total_rows": total_rows,
    }