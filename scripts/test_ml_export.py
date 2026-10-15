"""Validasi statis untuk jembatan Feature Store -> ML (Tahap 2).

Tidak memanggil Spark, tidak membaca/menulis data, tidak menjalankan
pipeline. Hanya memeriksa kontrak kolom dan aturan angkatan_enc.
"""

import unittest

from backend.feature_store import ml_export as mx
from backend.feature_store.feature_engineering import FEATURE_X
from backend.ml import data_preparation as dp


class MlExportContractTests(unittest.TestCase):
    def test_angkatan_enc_rule_matches_existing_data(self):
        expected = {
            2012: 0, 2013: 0, 2014: 0, 2015: 0,
            2016: 1, 2017: 1, 2018: 1,
            2019: 2, 2020: 2, 2021: 2,
            2022: 2, 2023: 2, 2024: 2,
        }
        for angkatan, enc in expected.items():
            self.assertEqual(mx.encode_angkatan_value(angkatan), enc)

    def test_angkatan_enc_none(self):
        self.assertIsNone(mx.encode_angkatan_value(None))

    def test_rename_map(self):
        self.assertEqual(mx.ML_RENAME_MAP, {"IPK_kategori": "ipk_kategori"})

    def test_source_columns(self):
        self.assertEqual(
            mx.FS_TRAINING_COLUMNS, ["id_mahasiswa", *FEATURE_X, "label"]
        )
        self.assertEqual(mx.FS_INFERENCE_COLUMNS, ["id_mahasiswa", *FEATURE_X])

    def test_ml_columns_include_model_features(self):
        for feature in dp.MODEL_A_CAT + dp.MODEL_A_NUM:
            self.assertIn(feature, mx.ML_FEATURE_COLUMNS)
        for feature in dp.MODEL_B_CAT + dp.MODEL_B_NUM:
            self.assertIn(feature, mx.ML_FEATURE_COLUMNS)

    def test_ml_column_shapes(self):
        self.assertEqual(
            mx.ML_TRAINING_COLUMNS,
            ["id_mahasiswa", *mx.ML_FEATURE_COLUMNS, "label"],
        )
        self.assertEqual(
            mx.ML_INFERENCE_COLUMNS, ["id_mahasiswa", *mx.ML_FEATURE_COLUMNS]
        )
        self.assertNotIn("label", mx.ML_INFERENCE_COLUMNS)
        self.assertEqual(len(mx.ML_FEATURE_COLUMNS), len(set(mx.ML_FEATURE_COLUMNS)))

    def test_no_capital_ipk_column(self):
        self.assertNotIn("IPK_kategori", mx.ML_FEATURE_COLUMNS)
        self.assertIn("ipk_kategori", mx.ML_FEATURE_COLUMNS)

    def test_export_disabled_by_default(self):
        self.assertIsNone(mx.export_ml_datasets())


if __name__ == "__main__":
    unittest.main()
