from pyspark.ml.evaluation import MulticlassClassificationEvaluator

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def evaluate_model(training_result):
    """
    Mengevaluasi performa model Gaussian Naive Bayes.

    Parameters
    ----------
    training_result : dict
        Hasil output dari train_model()

    Returns
    -------
    dict
        Hasil evaluasi model
    """

    logger.info("=" * 60)
    logger.info("EVALUASI MODEL GAUSSIAN NAIVE BAYES")
    logger.info("=" * 60)

    # =====================================================
    # Prediction Test
    # =====================================================

    prediction_df = training_result["prediction_test"]

    # =====================================================
    # Accuracy
    # =====================================================

    accuracy = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    ).evaluate(prediction_df)

    # =====================================================
    # Precision
    # =====================================================

    precision = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="weightedPrecision"
    ).evaluate(prediction_df)

    # =====================================================
    # Recall
    # =====================================================

    recall = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="weightedRecall"
    ).evaluate(prediction_df)

    # =====================================================
    # F1 Score
    # =====================================================

    f1_score = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="f1"
    ).evaluate(prediction_df)

    logger.info("=" * 60)
    logger.info("HASIL EVALUASI")
    logger.info("=" * 60)

    logger.info(f"Accuracy  : {accuracy:.4f}")
    logger.info(f"Precision : {precision:.4f}")
    logger.info(f"Recall    : {recall:.4f}")
    logger.info(f"F1 Score  : {f1_score:.4f}")

    # =====================================================
    # Confusion Matrix
    # =====================================================

    logger.info("=" * 60)
    logger.info("CONFUSION MATRIX")
    logger.info("=" * 60)

    confusion_matrix = (
        prediction_df
        .groupBy(
            "label",
            "prediction"
        )
        .count()
        .orderBy(
            "label",
            "prediction"
        )
    )

    confusion_matrix.show(truncate=False)

    logger.info("=" * 60)
    logger.info("EVALUASI SELESAI")
    logger.info("=" * 60)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "confusion_matrix": confusion_matrix,
        "prediction_df": prediction_df,

        # hasil training
        "model": training_result["model"],
        "cross_validator": training_result["cross_validator"],
        "feature_pipeline_model": training_result["feature_pipeline_model"],
        "label_order": training_result.get("label_order", []),

        # dataset
        "prepared_df": training_result["prepared_df"],
        "train_df": training_result["train_df"],
        "test_df": training_result["test_df"],

        # statistik
        "train_count": training_result["train_count"],
        "test_count": training_result["test_count"],
        "total_rows": training_result["total_rows"]
    }