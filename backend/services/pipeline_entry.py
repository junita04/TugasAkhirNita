"""
Entry point pipeline tanpa HTTP/FastAPI.

Menyediakan resolusi file Excel di folder ``data/`` dan eksekusi pipeline
langsung, dipakai oleh CLI ``scripts/run_pipeline.py`` dan Airflow.
"""

from pathlib import Path

from backend.config.settings import DATA_DIR
from backend.services.pipeline_service import run_pipeline
from backend.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_FILENAME = "(asli)req_data_rut (1).xlsx"


def resolve_pipeline_file(filename: str = DEFAULT_FILENAME) -> Path:
    candidate = Path(filename)
    if candidate.name != filename or candidate.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("filename must be a local Excel filename")

    file_path = (DATA_DIR / candidate).resolve()
    data_root = DATA_DIR.resolve()
    if data_root not in file_path.parents or not file_path.is_file():
        raise ValueError("pipeline file does not exist under data/")
    return file_path


def run_pipeline_for_file(filename: str = DEFAULT_FILENAME) -> dict[str, str]:
    file_path = resolve_pipeline_file(filename)
    run_pipeline(file_path)
    return {"status": "success", "file": file_path.name}
