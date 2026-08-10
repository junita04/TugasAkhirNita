"""
Layanan status pipeline untuk halaman Pipeline Monitoring.

Menyimpan status setiap tahap pipeline (Waiting/Running/Success/Failed)
dalam memori agar dapat ditampilkan real-time dari endpoint.
"""

import threading
from datetime import datetime
from typing import Literal

from backend.utils.logger import get_logger

logger = get_logger(__name__)

StageStatus = Literal["waiting", "running", "success", "failed"]

STAGES = (
    "bronze",
    "silver",
    "gold",
    "feature_store",
    "training",
    "evaluation",
    "registry",
    "prediction",
)

_lock = threading.Lock()
_state = {
    "stages": {stage: {"status": "waiting", "message": "", "updated": None} for stage in STAGES},
    "running": False,
    "started_at": None,
    "finished_at": None,
    "filename": None,
}


def reset(filename: str | None = None) -> None:
    global _state
    with _lock:
        _state = {
            "stages": {stage: {"status": "waiting", "message": "", "updated": None} for stage in STAGES},
            "running": False,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": None,
            "filename": filename,
        }


def start(filename: str | None = None) -> None:
    with _lock:
        _state["running"] = True
        _state["started_at"] = datetime.now().isoformat(timespec="seconds")
        _state["finished_at"] = None
        _state["filename"] = filename
        for stage in STAGES:
            _state["stages"][stage] = {"status": "waiting", "message": "", "updated": None}


def set_stage(stage: str, status: StageStatus, message: str = "") -> None:
    if stage not in STAGES:
        return
    with _lock:
        _state["stages"][stage] = {
            "status": status,
            "message": message,
            "updated": datetime.now().isoformat(timespec="seconds"),
        }


def finish(success: bool = True) -> None:
    with _lock:
        _state["running"] = False
        _state["finished_at"] = datetime.now().isoformat(timespec="seconds")
        if not success:
            for stage in STAGES:
                if _state["stages"][stage]["status"] == "waiting":
                    _state["stages"][stage]["status"] = "failed"
                    _state["stages"][stage]["message"] = "Pipeline gagal sebelum tahap ini"


def get_state() -> dict:
    with _lock:
        return {
            "stages": {k: dict(v) for k, v in _state["stages"].items()},
            "running": _state["running"],
            "started_at": _state["started_at"],
            "finished_at": _state["finished_at"],
            "filename": _state["filename"],
        }
