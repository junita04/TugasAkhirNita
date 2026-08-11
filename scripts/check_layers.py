"""
CLI: verifikasi seluruh layer hasil pipeline.

    python scripts/check_layers.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


LAYERS = (
    "bronze",
    "silver",
    "gold",
    "feature_store",
)


def main() -> None:
    from backend.spark.session import get_spark
    from backend.config.settings import ICEBERG_NAMESPACE

    spark = get_spark("Check Layers")

    print("=" * 60)
    print(f"CATALOG : {ICEBERG_NAMESPACE}")
    print("=" * 60)

    for layer in LAYERS:
        tables = spark.sql(
            f"SHOW TABLES IN {ICEBERG_NAMESPACE}.{layer}"
        ).collect()

        print(f"\n[{layer}] ({len(tables)} tabel)")

        for row in sorted(tables, key=lambda r: r.tableName):
            full = f"{ICEBERG_NAMESPACE}.{layer}.{row.tableName}"
            try:
                count = spark.table(full).count()
            except Exception as exc:
                count = f"ERROR: {exc}"
            print(f"  - {row.tableName:<40} rows={count}")

    spark.stop()


if __name__ == "__main__":
    main()
