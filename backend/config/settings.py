from pathlib import Path # untuk membaca folder dan file
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2] # mencari folder utama


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


_load_env_file(PROJECT_ROOT / ".env")

# membuat sederhana folder (directory)

DATA_DIR = PROJECT_ROOT / "data"
ICEBERG_DIR = PROJECT_ROOT / "iceberg"
MODEL_DIR = PROJECT_ROOT / "models"
LOG_DIR = PROJECT_ROOT / "logs"
SPARK_EVENT_DIR = PROJECT_ROOT / "spark-events"
SCRIPT_DIR = PROJECT_ROOT / "scripts"
STATIC_DIR = PROJECT_ROOT / "static"

# bagian spark 

APP_NAME = "Prediksi Kelulusan Mahasiswa" # nama spark application

MASTER = "local[*]" # memakai seluruh core CPU

SPARK_EVENT_LOG = True # mencatat history (True) kalau tidak mencatat (False)

SPARK_EVENT_DIR.mkdir(parents=True, exist_ok=True)
SPARK_EVENT_LOG_DIR = SPARK_EVENT_DIR.as_uri() # hasil log akan disimpan di folder spark-events

SPARK_HISTORY_UI = "http://localhost:18080" # localhost history spark

# PostgreSQL serving layer untuk Apache Superset
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "academic_serving")
POSTGRES_USER = os.getenv("POSTGRES_USER", "academic")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change-me")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "public")
