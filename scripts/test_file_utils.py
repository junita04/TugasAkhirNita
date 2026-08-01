from pathlib import Path

from backend.utils.file_utils import (
    ensure_directory,
    file_exists,
    list_files,
)

folder = Path("test_folder")

ensure_directory(folder)

print("Folder dibuat :", folder.exists())

print("README ada :", file_exists(Path("README.md")))

print("Isi project:")

for file in list_files(Path(".")):
    print("-", file.name)