import json

from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    join_gold_dataset,
    FEATURE_X,
)
from backend.feature_store.training_dataset import (
    create_training_dataset,
)
from backend.feature_store.inference_dataset import (
    create_inference_dataset,
)
from backend.config.settings import LOG_DIR

logger = get_logger(__name__)


def run_feature_store():

    logger.info("=" * 60)
    logger.info("MEMULAI FEATURE STORE (Tahap 4)")
    logger.info("=" * 60)

    # ==========================================
    # JOIN Gold Star Schema
    # ==========================================

    joined, join_report = join_gold_dataset()

    # ==========================================
    # Training Dataset (mahasiswa LULUS)
    # ==========================================

    logger.info("Membuat Training Dataset...")

    training_df, training_report = create_training_dataset(joined)

    # ==========================================
    # Inference Dataset (mahasiswa AKTIF)
    # ==========================================

    logger.info("Membuat Inference Dataset...")

    inference_df, inference_report = create_inference_dataset(joined)

    # ==========================================
    # Kumpulkan laporan + simpan DQR Feature Store
    # ==========================================

    quality_report = {
        "join": join_report,
        "training": training_report,
        "inference": inference_report,
        "feature_x": FEATURE_X,
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = LOG_DIR / "feature_store_quality_report.json"

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(quality_report, fh, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Feature Store Quality Report : {json_path}")

    # ==========================================
    # Laporan ringkas
    # ==========================================

    print()
    print("=" * 88)
    print("FEATURE STORE - LAPORAN VALIDASI")
    print("=" * 88)

    print("# JOIN RESULT")
    print(f"  total            : {join_report['join_total']}")
    print(f"  distinct ID      : {join_report['join_distinct']}")
    print(f"  duplicate        : {join_report['join_duplicate']}")
    print(f"  row multiplication: {join_report['row_multiplication']}")

    print()
    print("# TRAINING DATASET (LULUS)")
    print(f"  jumlah awal LULUS : {training_report['jumlah_awal_lulus']}")
    print(f"  jumlah valid      : {training_report['jumlah_valid']}")
    print(f"  jumlah tanpa KHS  : {training_report['jumlah_tanpa_khs']}")
    print(f"  label Tepat Waktu : {training_report['label_tepat_waktu']}")
    print(f"  label Terlambat   : {training_report['label_terlambat']}")
    print(f"  duplicate ID      : {training_report['duplicate_id']}")
    print(f"  leakage           : forbidden={training_report['leakage_forbidden']} "
          f"extra={training_report['leakage_extra']}")

    print()
    print("# INFERENCE DATASET (AKTIF)")
    print(f"  jumlah awal AKTIF : {inference_report['jumlah_awal_aktif']}")
    print(f"  jumlah valid      : {inference_report['jumlah_valid']}")
    print(f"  jumlah tanpa KHS  : {inference_report['jumlah_tanpa_khs']}")
    print(f"  duplicate ID      : {inference_report['duplicate_id']}")
    print(f"  leakage           : forbidden={inference_report['leakage_forbidden']} "
          f"extra={inference_report['leakage_extra']}")

    print()
    print("# FEATURE SCHEMA (X)")
    print(f"  {FEATURE_X}")

    forbidden_total = (
        len(training_report["leakage_forbidden"])
        + len(inference_report["leakage_forbidden"])
        + len(training_report["leakage_extra"])
        + len(inference_report["leakage_extra"])
    )
    print(f"  Forbidden features detected: {forbidden_total}")
    print("=" * 88)

    return quality_report
