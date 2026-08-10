from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config.settings import DATA_DIR
from backend.services.pipeline_service import run_pipeline


router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


class PipelineRequest(BaseModel):
    filename: str = "req_data_rut.xlsx"


def resolve_pipeline_file(filename: str = "req_data_rut.xlsx") -> Path:
    candidate = Path(filename)
    if candidate.name != filename or candidate.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("filename must be a local Excel filename")

    file_path = (DATA_DIR / candidate).resolve()
    data_root = DATA_DIR.resolve()
    if data_root not in file_path.parents or not file_path.is_file():
        raise ValueError("pipeline file does not exist under data/")
    return file_path


def run_pipeline_for_file(filename: str = "req_data_rut.xlsx") -> dict[str, str]:
    file_path = resolve_pipeline_file(filename)
    run_pipeline(file_path)
    return {"status": "success", "file": file_path.name}


@router.post("/run")
def trigger_pipeline(request: PipelineRequest | None = None) -> dict[str, str]:
    filename = request.filename if request is not None else "req_data_rut.xlsx"
    try:
        return run_pipeline_for_file(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="pipeline failed") from exc


@router.get("/state")
def pipeline_state() -> dict:
    """
    Status setiap tahap pipeline (Waiting/Running/Success/Failed)
    untuk halaman Pipeline Monitoring.
    """
    from backend.services import pipeline_state
    return pipeline_state.get_state()


@router.post("/start")
def start_pipeline(request: PipelineRequest | None = None) -> dict:
    """
    Menjalankan pipeline secara asynchronous dengan pelaporan status
    per tahap (Bronze -> Silver -> Gold -> Feature Store). Response
    langsung kembali; pantau lewat GET /pipeline/state.
    """
    filename = request.filename if request is not None else "req_data_rut.xlsx"
    try:
        file_path = resolve_pipeline_file(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    from backend.services.pipeline_runner import start_pipeline_async
    start_pipeline_async(file_path)
    return {"status": "success", "file": file_path.name, "async": True}
