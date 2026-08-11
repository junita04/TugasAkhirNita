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


def _spark_mode() -> str:
    value = os.getenv("SPARK_MODE", "local").strip().lower()
    if value not in {"local", "cluster"}:
        raise ValueError("SPARK_MODE must be either 'local' or 'cluster'")
    return value


SPARK_MODE = _spark_mode()
MASTER = os.getenv(
    "SPARK_MASTER_URL",
    "local[*]" if SPARK_MODE == "local" else "spark://spark-master:7077",
)

SPARK_EVENT_LOG = os.getenv("SPARK_EVENT_LOG", "true").lower() == "true" # mencatat history

SPARK_EVENT_DIR.mkdir(parents=True, exist_ok=True)
SPARK_EVENT_LOG_DIR = SPARK_EVENT_DIR.as_uri() # hasil log akan disimpan di folder spark-events

SPARK_HISTORY_UI = os.getenv("SPARK_HISTORY_UI", "http://localhost:18080") # localhost history spark

# Iceberg catalog
# 'local'   -> warehouse folder filesystem (iceberg/)
# 'iceberg' -> Hive Metastore + warehouse di MinIO (s3a://warehouse/iceberg)
ICEBERG_CATALOG = os.getenv(
    "ICEBERG_CATALOG",
    "local" if SPARK_MODE == "local" else "iceberg",
)
ICEBERG_NAMESPACE = ICEBERG_CATALOG
# Mode lokal memakai URI filesystem (file:///...) karena Hadoop di Windows
# tidak menangani path absolut ber-backslash tanpa scheme.
ICEBERG_WAREHOUSE = os.getenv(
    "ICEBERG_WAREHOUSE",
    ICEBERG_DIR.as_uri() if SPARK_MODE == "local" else "s3a://warehouse/iceberg",
)

# MinIO (S3) credential untuk mode cluster
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin-password")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_PATH_STYLE_ACCESS = os.getenv("S3_PATH_STYLE_ACCESS", "true").lower() == "true"

# Hive Metastore
HIVE_METASTORE_URI = os.getenv("HIVE_METASTORE_URI", "thrift://hive-metastore:9083")

# PostgreSQL serving layer untuk Apache Superset
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() == "true"
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "academic_serving")
POSTGRES_USER = os.getenv("POSTGRES_USER", "academic")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change-me")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "public")
