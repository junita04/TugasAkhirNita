from pathlib import Path

import pandas as pd


def read_excel(file_path: Path, sheet_name=0) -> pd.DataFrame:
    """
    Membaca file Excel dan mengembalikan DataFrame.
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)