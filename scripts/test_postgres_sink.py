import os
import unittest
from unittest.mock import patch

from backend.serving.postgres_sink import (
    GOLD_TABLES,
    postgres_jdbc_url,
    postgres_properties,
)


class PostgresSinkTests(unittest.TestCase):
    def test_jdbc_url_uses_environment_values(self):
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "analytics",
        }, clear=False):
            self.assertEqual(
                postgres_jdbc_url(),
                "jdbc:postgresql://localhost:5433/analytics",
            )

    def test_table_mapping_is_fixed(self):
        self.assertEqual(
            [item.target_table for item in GOLD_TABLES],
            ["gold_mahasiswa", "gold_program_studi", "gold_kurikulum"],
        )

    def test_properties_do_not_return_an_empty_password(self):
        with patch.dict(os.environ, {
            "POSTGRES_USER": "academic",
            "POSTGRES_PASSWORD": "secret",
        }, clear=False):
            self.assertEqual(postgres_properties()["password"], "secret")


if __name__ == "__main__":
    unittest.main()
