"""
Layanan riwayat prediksi.

Menyimpan hasil prediksi sebagai file JSON di folder data/history
agar dapat ditampilkan, difilter, dan dicari pada halaman History.
"""

import json
import threading
from datetime import datetime
from pathlib import Path

from backend.config.settings import PROJECT_ROOT
from backend.utils.logger import get_logger

logger = get_logger(__name__)

HISTORY_DIR = PROJECT_ROOT / "data" / "history"
_lock = threading.Lock()


def _ensure_dir() -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _history_file() -> Path:
    return HISTORY_DIR / "predictions.json"


def save_prediction(record: dict) -> dict:
    """Menambahkan satu record prediksi ke riwayat."""
    _ensure_dir()

    with _lock:
        items = _load_all()
        record = dict(record)
        record.setdefault("id", int(datetime.now().timestamp() * 1000))
        record.setdefault("timestamp", datetime.now().isoformat(timespec="seconds"))
        items.append(record)
        with open(_history_file(), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    return record


def _load_all() -> list:
    _ensure_dir()
    path = _history_file()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def get_history(query: str | None = None, status: str | None = None) -> list:
    """Mengembalikan seluruh riwayat, dengan filter cari dan status."""
    items = _load_all()

    if query:
        q = query.strip().lower()
        items = [
            item for item in items
            if q in json.dumps(item, ensure_ascii=False).lower()
        ]

    if status:
        status = status.strip().lower()
        items = [
            item for item in items
            if str(item.get("prediction", "")).lower() == status
        ]

    items.sort(key=lambda item: str(item.get("timestamp", "")), reverse=True)
    return items


def clear_history() -> int:
    """Menghapus seluruh riwayat; mengembalikan jumlah yang terhapus."""
    _ensure_dir()
    with _lock:
        count = len(_load_all())
        if _history_file().exists():
            _history_file().unlink()
    return count
