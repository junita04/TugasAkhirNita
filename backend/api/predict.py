from fastapi import APIRouter

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)


@router.post("/")
def predict():
    """
    Endpoint prediksi.
    """

    return {
        "status": "success",
        "message": "Prediction API is running"
    }