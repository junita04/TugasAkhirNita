"""
Resolver isolasi pipeline (Tahap QA).

Modul ini menjadi SATU sumber kebenaran untuk:
  * namespace/skema Iceberg (bronze/silver/gold/feature_store), dan
  * direktori output (artifact model, Excel hasil, laporan JSON).

SEMUA DEFAULT MENUNJUK KE PRODUKSI. Jalur QA hanya aktif bila environment
variable ``PIPELINE_NS`` diisi (mis. ``qa``). Dengan demikian DAG produksi
yang sudah ada (prediction_pipeline, training_pipeline, inference_pipeline)
berjalan PERSIS seperti sebelumnya tanpa perubahan perilaku.

Contoh:
    # produksi (default)
    ns("gold")                 -> "hive_iceberg.gold"
    table("gold", "dim_mahasiswa") -> "hive_iceberg.gold.dim_mahasiswa"

    # QA
    PIPELINE_NS=qa
    ns("gold")                 -> "hive_iceberg.qa_gold"
    table("gold", "dim_mahasiswa") -> "hive_iceberg.qa_gold.dim_mahasiswa"

Catatan: fungsi namespace sengaja dievaluasi SAAT DIPANGGIL (bukan saat
import) agar proses yang sama dapat menargetkan produksi maupun QA dengan
mengubah environment terlebih dahulu.
"""

from __future__ import annotations

import os
from pathlib import Path

from backend.config.settings import DATA_DIR, LOG_DIR, MODEL_DIR

# Katalog HMS-backed agar tabel terlihat oleh Trino (konsisten dengan
# konvensi proyek yang sudah ada).
DEFAULT_CATALOG = "hive_iceberg"


def namespace_prefix() -> str:
    """Kembalikan prefix namespace (``""`` untuk produksi, ``"qa_"`` dst.)."""
    value = os.getenv("PIPELINE_NS", "").strip()
    if not value:
        return ""
    return value if value.endswith("_") else f"{value}_"


def ns(schema: str, catalog: str = DEFAULT_CATALOG) -> str:
    """Kembalikan ``catalog.[prefix]schema`` (mis. ``hive_iceberg.qa_gold``)."""
    return f"{catalog}.{namespace_prefix()}{schema}"


def table(schema: str, name: str, catalog: str = DEFAULT_CATALOG) -> str:
    """Kembalikan ``catalog.[prefix]schema.name``."""
    return f"{ns(schema, catalog)}.{name}"


# ============================================================
# Direktori output (default produksi, dapat dioverride untuk QA)
# ============================================================

def model_dir() -> Path:
    """Direktori artifact model (.joblib + metadata .json)."""
    return Path(os.getenv("PIPELINE_MODEL_DIR", str(MODEL_DIR)))


def ml_output_dir() -> Path:
    """Direktori Excel dataset/hasil ML (default: ``data/data fix``)."""
    return Path(os.getenv("PIPELINE_ML_OUTPUT_DIR", str(DATA_DIR / "data fix")))


def data_output_dir() -> Path:
    """Direktori output data umum (default: ``data``)."""
    return Path(os.getenv("PIPELINE_DATA_OUTPUT_DIR", str(DATA_DIR)))


def log_dir() -> Path:
    """Direktori laporan kualitas JSON."""
    return Path(os.getenv("PIPELINE_LOG_DIR", str(LOG_DIR)))
