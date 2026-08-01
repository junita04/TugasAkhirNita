import unittest

from backend.serving.postgres_sink import GOLD_TABLES


class SupersetConfigTests(unittest.TestCase):
    def test_all_published_tables_are_registered_targets(self):
        self.assertEqual(
            {spec.target_table for spec in GOLD_TABLES},
            {"gold_mahasiswa", "gold_program_studi", "gold_kurikulum"},
        )


if __name__ == "__main__":
    unittest.main()
