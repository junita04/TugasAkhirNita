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
from backend.config.namespaces import log_dir

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

    json_path = log_dir() / "feature_store_quality_report.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)

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
    print("# TRAINING DATASET (ANGKATAN 2012-2021)")
    print(f"  jumlah awal 2012-2021 : {training_report['jumlah_awal_angkatan_2012_2021']}")
    print(f"  jumlah lulus          : {training_report['jumlah_lulus']}")
    print(f"  aktif → label=1      : {training_report['jumlah_aktif_dilabeli_1']}")
    print(f"  IP NULL dikeluarkan  : {training_report['jumlah_ip_null_dikeluarkan']}")
    print(f"  jumlah valid         : {training_report['jumlah_valid']}")
    print(f"  label 0 Tepat Waktu  : {training_report['label_0_tepat_waktu']}")
    print(f"  label 1 Terlambat    : {training_report['label_1_terlambat']}")
    print(f"  duplicate ID         : {training_report['duplicate_id']}")
    print(f"  leakage              : forbidden={training_report['leakage_forbidden']} "
          f"extra={training_report['leakage_extra']}")
    if "angkatan_distribution" in training_report:
        for a, c in sorted(training_report["angkatan_distribution"].items()):
            print(f"    Angkatan {a}: {c}")

    print()
    print("# INFERENCE DATASET (ANGKATAN 2022-2024, AKTIF + LULUS)")
    print(f"  jumlah awal 2022-2024 : {inference_report['jumlah_awal_angkatan_2022_2024']}")
    print(f"  jumlah aktif          : {inference_report['jumlah_aktif']}")
    print(f"  jumlah lulus          : {inference_report['jumlah_lulus']}")
    print(f"  IP NULL dikeluarkan  : {inference_report['jumlah_ip_null_dikeluarkan']}")
    print(f"  jumlah valid         : {inference_report['jumlah_valid']}")
    print(f"  duplicate ID         : {inference_report['duplicate_id']}")
    print(f"  leakage              : forbidden={inference_report['leakage_forbidden']} "
          f"extra={inference_report['leakage_extra']}")
    if "angkatan_distribution" in inference_report:
        for a, c in sorted(inference_report["angkatan_distribution"].items()):
            print(f"    Angkatan {a}: {c}")

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
