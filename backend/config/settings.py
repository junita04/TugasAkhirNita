from pathlib import Path # untuk membaca folder dan file

PROJECT_ROOT = Path(__file__).resolve().parents[2] # mencari folder utama

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

SPARK_EVENT_LOG_DIR = f"file://{SPARK_EVENT_DIR}" # hasil log akan disimpan di folder spark-events

SPARK_HISTORY_UI = "http://localhost:18080" # localhost history spark