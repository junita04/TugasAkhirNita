"""Unit test untuk pelaporan kegagalan Bronze.

Tidak memanggil Spark dan tidak membaca/menulis data. Spark session,
validasi pandas, dan penulisan sheet di-mock, sehingga hanya logika
pelaporan keberhasilan/kegagalan yang diuji:

  - semua sheet berhasil  -> mengembalikan (success, skipped)
  - sheet kosong          -> masuk skipped, bukan failed
  - sheet gagal ditulis   -> menaikkan RuntimeError (task harus FAILED)
"""

import unittest
from unittest import mock

from backend.bronze import bronze


def _fake_excel(sheet_names):
    excel = mock.MagicMock()
    excel.sheet_names = sheet_names
    return excel


def _preview(rows=5):
    preview = mock.MagicMock()
    preview.__len__.return_value = rows
    return preview


class BronzeFailureReportingTests(unittest.TestCase):
    def _run(self, sheet_names, valid_sheets, write_side_effect):
        """Jalankan load_all_sheets_to_bronze dengan dependency di-mock."""
        with mock.patch.object(
            bronze.pd, "ExcelFile", return_value=_fake_excel(sheet_names)
        ), mock.patch.object(
            bronze,
            "_validate_sheet_pandas",
            side_effect=lambda _fp, sheet: (
                _preview() if sheet in valid_sheets else None
            ),
        ), mock.patch.object(
            bronze, "get_spark", return_value=mock.MagicMock()
        ), mock.patch.object(
            bronze, "_write_sheet", side_effect=write_side_effect
        ), mock.patch.object(
            bronze.time, "sleep", return_value=None
        ):
            return bronze.load_all_sheets_to_bronze("dummy.xlsx")

    def test_all_sheets_success_returns_tuple(self):
        names = ["Referensi Data Mahasiswa", "Data KHS"]
        write = lambda *a, **k: (10, 3, "hive_iceberg.bronze.x")
        success, skipped = self._run(names, names, write)
        self.assertEqual(
            success, ["data_referensi_mahasiswa", "data_khs"]
        )
        self.assertEqual(skipped, [])

    def test_empty_sheet_is_skipped_not_failed(self):
        names = ["Referensi Data Mahasiswa", "Sheet Kosong"]
        valid = ["Referensi Data Mahasiswa"]
        write = lambda *a, **k: (10, 3, "hive_iceberg.bronze.x")
        success, skipped = self._run(names, valid, write)
        self.assertEqual(success, ["data_referensi_mahasiswa"])
        self.assertEqual(skipped, ["Sheet Kosong"])

    def test_write_failure_raises_runtime_error(self):
        names = ["Data KHS"]
        write = mock.Mock(side_effect=RuntimeError("Spark write boom"))
        with self.assertRaises(RuntimeError) as ctx:
            self._run(names, names, write)
        self.assertIn("Data KHS", str(ctx.exception))

    def test_partial_failure_raises_and_names_sheet(self):
        names = ["Referensi Data Mahasiswa", "Data KHS"]
        write = mock.Mock(
            side_effect=[
                (10, 3, "hive_iceberg.bronze.data_referensi_mahasiswa"),
                RuntimeError("Spark write boom"),
            ]
        )
        with self.assertRaises(RuntimeError) as ctx:
            self._run(names, names, write)
        self.assertIn("Data KHS", str(ctx.exception))
        self.assertNotIn("Data KHS", ["data_referensi_mahasiswa"])


if __name__ == "__main__":
    unittest.main()
