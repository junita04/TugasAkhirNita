import sys
sys.path.insert(0, '/opt/airflow')
from backend.ml.inference import run_inference

# Run inference
result = run_inference(smoke_test=False)

print()
print('='*80)
print('INFERENCE STATUS')
print('='*80)
print(f"Status: {result['status']}")
print(f"Total prediction: {result['comparison']['total']}")
print(f"Agreement: {result['comparison']['agreement']} ({result['comparison']['agreement_rate']}%)")
