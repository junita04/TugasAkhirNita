"""Run ML Training Pipeline (both variants)."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.ml.evaluate import run_ml_pipeline

result = run_ml_pipeline()
print(f"\nML PIPELINE STATUS: {result['overall']}")
