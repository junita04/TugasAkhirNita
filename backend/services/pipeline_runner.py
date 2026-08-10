"""
Runner pipeline dengan pelaporan status per tahap.

Menjalankan fungsi-fungsi pipeline yang SAMA dengan backend.services.pipeline_service
(Bronze -> Silver -> Gold -> Publish PostgreSQL -> Feature Store) namun di dalam
thread background dan memperbarui status tahap agar dapat dipantau secara real-time
oleh halaman Pipeline Monitoring.

Fungsi dan urutan setiap modul inti tidak diubah.
"""

import threading
from pathlib import Path

from backend.services import pipeline_state
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _update_stage(stage: str, fn, *args, **kwargs):
    pipeline_state.set_stage(stage, "running", "Memproses...")
    try:
        result = fn(*args, **kwargs)
        pipeline_state.set_stage(stage, "success", "Selesai")
        return result
    except Exception as exc:
        pipeline_state.set_stage(stage, "failed", str(exc))
        raise


def start_pipeline_async(file_path: Path, run_ml: bool = False) -> None:
    """
    Menjalankan pipeline secara asynchronous dengan pelaporan status.

    Membuka thread background agar request tidak terblokir dan status setiap
    tahap dapat dipantau. Jika `run_ml=True`, tahap ML (training, evaluation,
    registry, prediction) ikut dijalankan.
    """

    def _worker():
        try:
            pipeline_state.start(str(file_path.name))

            from backend.bronze.bronze import load_all_sheets_to_bronze
            _update_stage("bronze", load_all_sheets_to_bronze, file_path)

            from backend.silver.silver import process_all_tables
            _update_stage("silver", process_all_tables)

            from backend.gold.gold import process_gold
            _update_stage("gold", process_gold)

            from backend.serving.postgres_sink import publish_gold_tables
            from backend.spark.session import get_spark
            _update_stage("gold", publish_gold_tables, get_spark("Gold PostgreSQL Publish"))

            from backend.feature_store.feature_store import run_feature_store
            _update_stage("feature_store", run_feature_store)

            if run_ml:
                from backend.ml.train import train_model
                training_result = _update_stage("training", train_model)

                from backend.ml.evaluate import evaluate_model
                evaluation_result = _update_stage("evaluation", evaluate_model, training_result)

                from backend.ml.registry import save_model
                _update_stage("registry", save_model, evaluation_result)

            pipeline_state.finish(success=True)
            logger.info("Pipeline async selesai.")
        except Exception:
            logger.exception("Pipeline async gagal.")
            pipeline_state.finish(success=False)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
