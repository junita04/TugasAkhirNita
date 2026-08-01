from fastapi import APIRouter

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/")
def get_dashboard():
    """
    Endpoint untuk memastikan Dashboard API berjalan.
    """

    return {
        "status": "success",
        "message": "Dashboard API is running"
    }