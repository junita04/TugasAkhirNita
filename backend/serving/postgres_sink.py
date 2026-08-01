"""Publish Gold Iceberg tables to PostgreSQL for analytics consumers."""

from dataclasses import dataclass
import os
import re
from typing import Any


@dataclass(frozen=True)
class GoldTableSpec:
    source_table: str
    target_table: str


GOLD_TABLES = (
    GoldTableSpec("local.gold.gold_mahasiswa", "gold_mahasiswa"),
    GoldTableSpec("local.gold.gold_program_studi", "gold_program_studi"),
    GoldTableSpec("local.gold.gold_kurikulum", "gold_kurikulum"),
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} wajib diisi")
    return value


def postgres_schema() -> str:
    schema = os.getenv("POSTGRES_SCHEMA", "public")
    if not _IDENTIFIER.fullmatch(schema):
        raise RuntimeError("POSTGRES_SCHEMA hanya boleh berisi identifier PostgreSQL yang valid")
    return schema


def postgres_jdbc_url() -> str:
    host = _required_env("POSTGRES_HOST")
    port = _required_env("POSTGRES_PORT")
    database = _required_env("POSTGRES_DB")
    return f"jdbc:postgresql://{host}:{port}/{database}"


def postgres_properties() -> dict[str, str]:
    return {
        "user": _required_env("POSTGRES_USER"),
        "password": _required_env("POSTGRES_PASSWORD"),
        "driver": "org.postgresql.Driver",
    }


def publish_gold_tables(spark: Any) -> None:
    """Write the fixed Gold tables to PostgreSQL as the latest serving snapshot."""

    url = postgres_jdbc_url()
    properties = postgres_properties()
    schema = postgres_schema()

    for table in GOLD_TABLES:
        target = f"{schema}.{table.target_table}"
        try:
            dataframe = spark.table(table.source_table)
            dataframe.write.jdbc(
                url=url,
                table=target,
                mode="overwrite",
                properties=properties,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Gagal publish {table.source_table} ke PostgreSQL table {target}"
            ) from exc
