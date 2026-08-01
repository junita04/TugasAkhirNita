import os
import unittest
from unittest.mock import patch

from docker.superset.trino_config import (
    TRINO_CATALOG,
    TRINO_DATABASE_NAME,
    TRINO_SCHEMA,
    TRINO_TABLES,
    dataset_specs,
    trino_uri,
)


class SupersetConfigTests(unittest.TestCase):
    def test_trino_uri_uses_internal_defaults(self):
        with patch.dict(os.environ, {}, clear=False):
            for key in ("TRINO_HOST", "TRINO_PORT", "TRINO_USER", "TRINO_CATALOG"):
                os.environ.pop(key, None)
            self.assertEqual(trino_uri(), "trino://trino@trino:8082/iceberg")

    def test_trino_uri_supports_environment_overrides(self):
        with patch.dict(
            os.environ,
            {
                "TRINO_HOST": "trino.internal",
                "TRINO_PORT": "8443",
                "TRINO_USER": "analytics user",
                "TRINO_CATALOG": "lakehouse",
            },
        ):
            self.assertEqual(
                trino_uri(),
                "trino://analytics+user@trino.internal:8443/lakehouse",
            )

    def test_registered_tables_are_gold_tables(self):
        self.assertEqual(TRINO_DATABASE_NAME, "Academic Trino")
        self.assertEqual(TRINO_CATALOG, "iceberg")
        self.assertEqual(TRINO_SCHEMA, "gold")
        self.assertEqual(
            set(TRINO_TABLES),
            {"gold_mahasiswa", "gold_program_studi", "gold_kurikulum"},
        )

    def test_dataset_specs_target_trino_gold_tables(self):
        self.assertEqual(
            dataset_specs(),
            [
                ("gold", "gold_mahasiswa"),
                ("gold", "gold_program_studi"),
                ("gold", "gold_kurikulum"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
