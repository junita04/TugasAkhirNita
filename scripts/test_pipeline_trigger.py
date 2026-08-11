import unittest
from unittest.mock import patch

from pathlib import Path

from backend.services.pipeline_entry import resolve_pipeline_file, run_pipeline_for_file


class PipelineTriggerTests(unittest.TestCase):
    def test_runs_default_original_dataset(self):
        with patch("backend.services.pipeline_entry.run_pipeline") as run_pipeline:
            result = run_pipeline_for_file()

        self.assertEqual(result["file"], "req_data_rut.xlsx")
        run_pipeline.assert_called_once_with((Path.cwd() / "data" / "req_data_rut.xlsx").resolve())

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            resolve_pipeline_file("../.env")


if __name__ == "__main__":
    unittest.main()
