from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ComposeArchitectureTests(unittest.TestCase):
    def test_superset_waits_for_trino_and_receives_trino_settings(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("trino:\n        condition: service_healthy", compose)
        self.assertIn("TRINO_HOST: ${TRINO_HOST:-trino}", compose)
        self.assertIn("TRINO_CATALOG: ${TRINO_CATALOG:-iceberg}", compose)

    def test_env_example_declares_docker_based_cluster_and_trino_values(self):
        env = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("SPARK_MODE=cluster", env)
        self.assertIn("SPARK_MASTER_URL=spark://spark-master:7077", env)
        self.assertIn("S3_ENDPOINT=http://minio:9000", env)
        self.assertIn("HIVE_METASTORE_URI=thrift://hive-metastore:9083", env)
        self.assertIn("TRINO_URI=http://trino:8082", env)
        self.assertIn("TRINO_CATALOG=iceberg", env)

    def test_spark_docker_services_are_optional(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        for service in ("spark-master:", "spark-worker:", "spark-history:"):
            start = compose.index(f"  {service}")
            end = compose.find("\n  #", start + 1)
            section = compose[start:] if end == -1 else compose[start:end]
            self.assertIn("profiles: [spark-docker]", section)

    def test_airflow_uses_host_fastapi_trigger_for_local_spark(self):
        dag = (PROJECT_ROOT / "docker" / "airflow" / "dags" / "prediction_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("host.docker.internal:8000/pipeline/run", dag)
        self.assertNotIn("SparkSubmitOperator", dag)

    def test_superset_init_does_not_inherit_web_healthcheck(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        start = compose.index("  superset-init:")
        end = compose.index("\n  superset:", start)
        self.assertIn("healthcheck:", compose[start:end])
        self.assertIn("disable: true", compose[start:end])


if __name__ == "__main__":
    unittest.main()
