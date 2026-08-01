from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ComposeArchitectureTests(unittest.TestCase):
    def test_superset_waits_for_trino_and_receives_trino_settings(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("trino:\n        condition: service_healthy", compose)
        self.assertIn("TRINO_HOST: ${TRINO_HOST:-trino}", compose)
        self.assertIn("TRINO_CATALOG: ${TRINO_CATALOG:-iceberg}", compose)

    def test_env_example_declares_local_cluster_and_trino_values(self):
        env = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("SPARK_MODE=local", env)
        self.assertIn("TRINO_URI=http://trino:8082", env)
        self.assertIn("TRINO_CATALOG=iceberg", env)


if __name__ == "__main__":
    unittest.main()
