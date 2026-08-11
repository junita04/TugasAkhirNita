"""
CLI: prediksi mahasiswa aktif (inference dataset) dan simpan hasil ke Iceberg.

    python scripts/run_prediction.py
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prediksi inference dataset dan simpan ke feature_store.prediction_result"
    )
    args = parser.parse_args()

    from backend.ml.predict import predict

    result_df = predict()

    total = result_df.count()
    distribution = (
        result_df.groupBy("prediction_label")
        .count()
        .orderBy("prediction_label")
        .collect()
    )

    print("=" * 60)
    print("HASIL PREDICTION")
    print("=" * 60)
    print(f"Total Mahasiswa Diprediksi : {total}")

    for row in distribution:
        print(f"{row['prediction_label']:<15}: {row['count']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
