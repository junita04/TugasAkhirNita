import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


RUNTIME_KEYS = (
    "SPARK_MODE",
    "SPARK_MASTER_URL",
    "ICEBERG_CATALOG",
    "ICEBERG_WAREHOUSE",
)


class FakeBuilder:
    def __init__(self):
        self.values = {}

    def config(self, key, value):
        self.values[key] = value
        return self


class SparkSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import backend.config.settings as settings

        cls.settings = settings

    def setUp(self):
        self.original_values = {key: os.environ.get(key) for key in RUNTIME_KEYS}

    def tearDown(self):
        for key, value in self.original_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(self.settings)

    def load_settings(self, values):
        for key in RUNTIME_KEYS:
            os.environ.pop(key, None)
        os.environ.update(values)
        return importlib.reload(self.settings)

    def test_local_profile_defaults_to_local_master_and_filesystem_catalog(self):
        settings = self.load_settings({"SPARK_MODE": "local"})

        self.assertEqual(settings.SPARK_MODE, "local")
        self.assertEqual(settings.MASTER, "local[*]")
        self.assertEqual(settings.ICEBERG_CATALOG, "local")
        self.assertTrue(settings.ICEBERG_WAREHOUSE.endswith("iceberg"))

    def test_cluster_profile_defaults_to_docker_master_and_hive_warehouse(self):
        settings = self.load_settings({"SPARK_MODE": "cluster"})

        self.assertEqual(settings.SPARK_MODE, "cluster")
        self.assertEqual(settings.MASTER, "spark://spark-master:7077")
        self.assertEqual(settings.ICEBERG_CATALOG, "iceberg")
        self.assertEqual(settings.ICEBERG_WAREHOUSE, "s3a://warehouse/iceberg")

    def test_explicit_runtime_values_override_profile_defaults(self):
        settings = self.load_settings(
            {
                "SPARK_MODE": "cluster",
                "SPARK_MASTER_URL": "spark://external-master:7077",
                "ICEBERG_CATALOG": "custom",
                "ICEBERG_WAREHOUSE": "s3a://custom/warehouse",
            }
        )

        self.assertEqual(settings.MASTER, "spark://external-master:7077")
        self.assertEqual(settings.ICEBERG_CATALOG, "custom")
        self.assertEqual(settings.ICEBERG_WAREHOUSE, "s3a://custom/warehouse")

    def test_invalid_spark_mode_fails_with_actionable_error(self):
        with self.assertRaisesRegex(ValueError, "SPARK_MODE"):
            self.load_settings({"SPARK_MODE": "standalone"})


class SparkBuilderTests(unittest.TestCase):
    def test_local_catalog_uses_hadoop_warehouse(self):
        from backend.spark import session

        builder = FakeBuilder()
        with patch.object(session, "ICEBERG_CATALOG", "local"), patch.object(
            session, "ICEBERG_WAREHOUSE", "D:/data/iceberg"
        ):
            session._iceberg_configs(builder)

        self.assertEqual(builder.values["spark.sql.catalog.local.type"], "hadoop")
        self.assertEqual(
            builder.values["spark.sql.catalog.local.warehouse"], "D:/data/iceberg"
        )

    def test_cluster_catalog_uses_hive_and_s3a(self):
        from backend.spark import session

        builder = FakeBuilder()
        with patch.object(session, "ICEBERG_CATALOG", "iceberg"), patch.object(
            session, "ICEBERG_WAREHOUSE", "s3a://warehouse/iceberg"
        ):
            session._iceberg_configs(builder)

        self.assertEqual(builder.values["spark.sql.catalog.iceberg.type"], "hive")
        self.assertEqual(
            builder.values["spark.sql.catalog.iceberg.uri"], session.HIVE_METASTORE_URI
        )
        self.assertEqual(
            builder.values["spark.hadoop.fs.s3a.endpoint"], session.S3_ENDPOINT
        )


class CatalogNamespaceTests(unittest.TestCase):
    def test_gold_table_specs_use_active_catalog(self):
        from backend.serving import postgres_sink

        with patch.object(postgres_sink, "ICEBERG_NAMESPACE", "iceberg"):
            self.assertEqual(
                postgres_sink.gold_source_table("gold_mahasiswa"),
                "iceberg.gold.gold_mahasiswa",
            )


if __name__ == "__main__":
    if os.getenv("RUN_SPARK_SMOKE") == "1":
        from backend.spark.session import get_spark

        spark = get_spark("Spark Local Smoke Test")
        print(f"Spark master: {spark.sparkContext.master}")
        print(f"Spark version: {spark.version}")
        spark.stop()
    else:
        unittest.main()
