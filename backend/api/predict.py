from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.prediction_service import predict_single
from backend.services.history_service import save_prediction
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)


class PredictRequest(BaseModel):
    nama: str = ""
    jenis_kelamin: str = "L"
    estimasi_semester: int = 8
    ipk: float = 0.0
    total_sks: int = 0
    jumlah_mk: int = 0
    persentase_sks: float = 0.0


@router.post("/")
def predict():
    """
    Endpoint prediksi.
    """

    return {
        "status": "success",
        "message": "Prediction API is running"
    }


class PredictDatasetRequest(BaseModel):
    filename: str


@router.post("/dataset")
def predict_dataset(request: PredictDatasetRequest):
    """
    Prediksi batch terhadap dataset Excel yang sudah diunggah ke folder data/.
    Menggunakan model yang sudah ada (tidak mengubah proses training).
    """

    try:
        from backend.services.batch_prediction_service import predict_dataset as run_batch

        result = run_batch(request.filename)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediksi batch gagal.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/submit")
def predict_submit(request: PredictRequest):
    """
    Prediksi status kelulusan satu mahasiswa dan simpan ke riwayat.
    """

    try:
        result = predict_single(request.model_dump())

        record = {
            **request.model_dump(),
            "prediction": result["prediction"],
            "probability_tepat": result.get("probability_tepat"),
            "probability_terlambat": result.get("probability_terlambat"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        saved = save_prediction(record)

        return {
            "status": "success",
            "message": "Prediksi berhasil.",
            "nama": result["nama"],
            "prediction": result["prediction"],
            "probability_tepat": result.get("probability_tepat"),
            "probability_terlambat": result.get("probability_terlambat"),
            "model_available": result.get("model_available", True),
            "timestamp": saved.get("timestamp"),
            "id": saved.get("id"),
        }
    except Exception as exc:
        logger.exception("Prediksi gagal.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
