"""Run Feature Store processing."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.feature_store.feature_store import run_feature_store

result = run_feature_store()
print(f"\nFeature Store completed successfully.")
