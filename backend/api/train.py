from fastapi import APIRouter, HTTPException

from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/train",
    tags=["Training"]
)


@router.post("/")
def train_model():
    """
    Endpoint training model.
    """

    return {
        "status": "success",
        "message": "Training API is running"
    }


@router.post("/run")
def run_training():
    """
    Menjalankan pelatihan Gaussian Naive Bayes penuh:
    data preparation -> train -> evaluate -> registry.

    Memanggil modul inti backend/ml/* tanpa mengubah logikanya.
    """

    try:
        from backend.ml.train import train_model as _train
        from backend.ml.evaluate import evaluate_model
        from backend.ml.registry import save_model
        from backend.services.training_metrics import compute_roc

        training_result = _train()
        evaluation_result = evaluate_model(training_result)
        save_model(evaluation_result)

        confusion_matrix = evaluation_result["confusion_matrix"]

        cm_rows = confusion_matrix.collect()
        labels = sorted({r["label"] for r in cm_rows} | {r["prediction"] for r in cm_rows})
        index_of = {label: i for i, label in enumerate(labels)}
        matrix = [
            [0] * len(labels)
            for _ in labels
        ]
        for r in cm_rows:
            i = index_of.get(r["label"])
            j = index_of.get(r["prediction"])
            if i is not None and j is not None:
                matrix[i][j] = int(r["count"])

        roc = compute_roc(evaluation_result["prediction_df"])

        return {
            "status": "success",
            "message": "Training selesai.",
            "train_count": training_result["train_count"],
            "test_count": training_result["test_count"],
            "total_rows": training_result["total_rows"],
            "smoothing": training_result["model"].getSmoothing(),
            "accuracy": evaluation_result["accuracy"],
            "precision": evaluation_result["precision"],
            "recall": evaluation_result["recall"],
            "f1": evaluation_result["f1_score"],
            "confusion_matrix": {"labels": labels, "matrix": matrix},
            "roc": roc,
        }
    except Exception as exc:
        logger.exception("Training gagal.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
