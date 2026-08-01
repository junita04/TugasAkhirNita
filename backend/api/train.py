from fastapi import APIRouter

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