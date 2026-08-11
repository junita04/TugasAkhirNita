"""
CLI: menjalankan pipeline ETL penuh tanpa FastAPI.

    python scripts/run_pipeline.py                    # default req_data_rut.xlsx
    python scripts/run_pipeline.py data/file_lain.xlsx
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Jalankan pipeline Bronze -> Silver -> Gold -> Feature Store"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Nama file Excel di folder data/ (default: req_data_rut.xlsx)",
    )
    args = parser.parse_args()

    from backend.services.pipeline_entry import (
        DEFAULT_FILENAME,
        resolve_pipeline_file,
    )
    from backend.services.pipeline_service import run_pipeline

    filename = args.file or DEFAULT_FILENAME

    if Path(filename).name == filename:
        file_path = resolve_pipeline_file(filename)
    else:
        file_path = Path(filename).resolve()
        if not file_path.is_file():
            print(f"File tidak ditemukan: {file_path}", file=sys.stderr)
            sys.exit(1)

    print(f"Pipeline file: {file_path}")
    run_pipeline(file_path)
    print("PIPELINE SELESAI")


if __name__ == "__main__":
    main()
