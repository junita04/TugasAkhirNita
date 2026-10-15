"""Run Inference on AKTIF students."""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.ml.inference import run_inference, print_report

result = run_inference(smoke_test=False)
print_report(result)
print(f"\nINFERENCE STATUS: {result['status']}")
