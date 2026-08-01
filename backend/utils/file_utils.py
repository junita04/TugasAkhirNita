from pathlib import Path


def ensure_directory(directory: Path) -> None:
    """
    Membuat folder jika belum ada.
    """
    directory.mkdir(parents=True, exist_ok=True)


def file_exists(file_path: Path) -> bool:
    """
    Mengecek apakah file ada.
    """
    return file_path.exists()


def list_files(directory: Path):
    """
    Mengambil daftar file dalam folder.
    """
    return [file for file in directory.iterdir() if file.is_file()]