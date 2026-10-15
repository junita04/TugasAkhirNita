import sys
sys.path.insert(0, '/opt/airflow')
from backend.ml.evaluate import run_ml_pipeline

# Run full ML pipeline
result = run_ml_pipeline()

print()
print('='*80)
print('PIPELINE STATUS')
print('='*80)
print(f"Overall status: {result['overall']}")
print(f"Without SMOTE: {result['without_smote']['status']}")
print(f"With SMOTE: {result['with_smote']['status']}")
