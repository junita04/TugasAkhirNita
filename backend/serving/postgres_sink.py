import os
from dataclasses import dataclass

from backend.config.settings import (
    ICEBERG_NAMESPACE,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_SCHEMA,
    POSTGRES_USER,
)


@dataclass(frozen=True)
class GoldTableSpec:
    source_table: str
    target_table: str


GOLD_TABLES = (
    GoldTableSpec(
        f"{ICEBERG_NAMESPACE}.gold.gold_mahasiswa",
        "gold_mahasiswa",
    ),
    GoldTableSpec(
        f"{ICEBERG_NAMESPACE}.gold.gold_program_studi",
        "gold_program_studi",
    ),
    GoldTableSpec(
        f"{ICEBERG_NAMESPACE}.gold.gold_kurikulum",
        "gold_kurikulum",
    ),
)


def gold_source_table(target_table: str) -> str:
    allowed_tables = {spec.target_table for spec in GOLD_TABLES}
    if target_table not in allowed_tables:
        raise ValueError(f"Unsupported Gold table: {target_table}")
    return f"{ICEBERG_NAMESPACE}.gold.{target_table}"


def postgres_jdbc_url() -> str:
    host = os.getenv("POSTGRES_HOST", POSTGRES_HOST)
    port = os.getenv("POSTGRES_PORT", POSTGRES_PORT)
    database = os.getenv("POSTGRES_DB", POSTGRES_DB)
    return f"jdbc:postgresql://{host}:{port}/{database}"


def postgres_properties() -> dict[str, str]:
    return {
        "user": os.getenv("POSTGRES_USER", POSTGRES_USER),
        "password": os.getenv("POSTGRES_PASSWORD", POSTGRES_PASSWORD),
        "driver": "org.postgresql.Driver",
    }


def publish_gold_tables(spark) -> None:
    schema = os.getenv("POSTGRES_SCHEMA", POSTGRES_SCHEMA)
    url = postgres_jdbc_url()
    properties = postgres_properties()

    for spec in GOLD_TABLES:
        target_table = spec.target_table
        try:
            dataframe = spark.table(gold_source_table(target_table))
            dataframe.write.jdbc(
                url=url,
                table=f"{schema}.{target_table}",
                mode="overwrite",
                properties=properties,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to publish Gold table {target_table} to PostgreSQL"
            ) from exc
