from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DataLakeRuntimeConfigurationTests(unittest.TestCase):
    def test_trino_uses_current_iceberg_hive_metastore_properties(self):
        config = (ROOT / "docker" / "trino" / "catalog" / "iceberg.properties").read_text()
        self.assertIn("iceberg.catalog.type=HIVE_METASTORE", config)
        self.assertNotIn("iceberg.catalog.type=hive\n", config)
        self.assertIn("fs.native-s3.enabled=true", config)
        self.assertNotIn("iceberg.hive-catalog.warehouse", config)

    def test_minio_init_seeds_original_dataset_into_raw_bucket(self):
        compose = (ROOT / "docker-compose.yml").read_text()
        init = (ROOT / "docker" / "minio" / "init.sh").read_text()
        self.assertIn("./data:/seed-data:ro", compose)
        self.assertIn("req_data_rut.xlsx", init)
        self.assertIn("local/${MINIO_BUCKET_RAW}/req_data_rut.xlsx", init)

    def test_spark_session_creates_pipeline_namespaces_before_writes(self):
        session = (ROOT / "backend" / "spark" / "session.py").read_text()
        self.assertIn("CREATE NAMESPACE IF NOT EXISTS", session)
        self.assertIn("org.apache.hadoop:hadoop-aws", session)
        self.assertIn("com.amazonaws:aws-java-sdk-bundle", session)
        self.assertIn("spark.hadoop.fs.s3a.fast.upload.buffer", session)
        self.assertIn("spark.local.dir", session)
        self.assertIn("spark.hadoop.fs.s3a.buffer.dir", session)
        for namespace in ("bronze", "silver", "gold", "feature_store"):
            self.assertIn(f'"{namespace}"', session)


if __name__ == "__main__":
    unittest.main()
