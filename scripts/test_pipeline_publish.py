import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.pipeline_service import run_pipeline


class PipelinePublishTests(unittest.TestCase):
    @patch("backend.services.pipeline_service.run_feature_store")
    @patch("backend.services.pipeline_service.publish_gold_tables")
    @patch("backend.services.pipeline_service.get_spark")
    @patch("backend.services.pipeline_service.process_gold")
    @patch("backend.services.pipeline_service.process_all_tables")
    @patch("backend.services.pipeline_service.load_all_sheets_to_bronze")
    def test_publish_runs_after_gold_before_feature_store(
        self, bronze, silver, gold, get_spark, publish, feature_store
    ):
        events = []
        gold.side_effect = lambda: events.append("gold")
        publish.side_effect = lambda spark: events.append("publish")
        feature_store.side_effect = lambda: events.append("feature_store")

        run_pipeline(Path("data/input.xlsx"))

        self.assertEqual(events, ["gold", "publish", "feature_store"])
        publish.assert_called_once_with(get_spark.return_value)


if __name__ == "__main__":
    unittest.main()
