import os
from urllib.parse import quote_plus


TRINO_DATABASE_NAME = "Academic Trino"
TRINO_CATALOG = "iceberg"
TRINO_SCHEMA = "gold"
TRINO_TABLES = ("gold_mahasiswa", "gold_program_studi", "gold_kurikulum")


def trino_uri() -> str:
    user = quote_plus(os.getenv("TRINO_USER", "trino"))
    host = os.getenv("TRINO_HOST", "trino")
    port = os.getenv("TRINO_PORT", "8082")
    catalog = os.getenv("TRINO_CATALOG", TRINO_CATALOG)
    return f"trino://{user}@{host}:{port}/{catalog}"


def dataset_specs() -> list[tuple[str, str]]:
    return [(TRINO_SCHEMA, table_name) for table_name in TRINO_TABLES]
