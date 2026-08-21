"""Unit tests for the idempotent Tahap 4A MinIO archive manifest."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_minio_artifacts import (
    archive_manifest,
    docker_copy_source,
    missing_relative_paths,
    recursive_list_command,
)


ROOT = Path(__file__).resolve().parents[1]


class MinioArtifactManifestTests(unittest.TestCase):
    def test_missing_relative_paths_syncs_only_objects_absent_from_minio(self):
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "already.parquet").write_text("existing")
            (source / "missing.parquet").write_text("missing")
            entry = type("Entry", (), {"source": source, "include_patterns": ("**/*",)})()

            missing = missing_relative_paths(entry, {"already.parquet"})

        self.assertEqual(missing, ["missing.parquet"])

    def test_recursive_listing_uses_mc_ls_not_find(self):
        command = recursive_list_command("warehouse/iceberg/bronze")

        self.assertEqual(
            command,
            ["mc", "ls", "--recursive", "--json", "local/warehouse/iceberg/bronze"],
        )
        self.assertNotIn("find", command)

    def test_docker_copy_source_uses_os_separator_not_path_class_attribute(self):
        source = docker_copy_source(Path("stage"))

        self.assertTrue(source.endswith("."))
        self.assertNotIn("Path.sep", source)

    def test_manifest_preserves_required_destination_structure(self):
        entries = archive_manifest(ROOT)
        destinations = {entry.destination for entry in entries}

        self.assertIn("warehouse/iceberg/bronze", destinations)
        self.assertIn("warehouse/iceberg/silver", destinations)
        self.assertIn("warehouse/iceberg/gold", destinations)
        self.assertIn("warehouse/iceberg/feature_store", destinations)
        self.assertIn("models/gaussian_nb/v3", destinations)
        self.assertIn("logs/timing", destinations)
        self.assertIn("logs/pipeline", destinations)

    def test_manifest_only_uses_existing_local_sources(self):
        entries = archive_manifest(ROOT)

        self.assertTrue(entries)
        self.assertTrue(all(entry.source.exists() for entry in entries))
        self.assertTrue(all(entry.source.is_dir() for entry in entries))


if __name__ == "__main__":
    unittest.main()
