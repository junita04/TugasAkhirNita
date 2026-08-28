import json, os, sys
sys.path.insert(0, "/opt/airflow")
from backend.config.settings import PROJECT_ROOT

models = {
    "4_features": os.path.join(PROJECT_ROOT, "models", "gaussian_nb_4_features", "metadata.json"),
    "8_features_without_smote": os.path.join(PROJECT_ROOT, "models", "gaussian_nb_8_features", "without_smote", "metadata.json"),
    "8_features_with_smote": os.path.join(PROJECT_ROOT, "models", "gaussian_nb_8_features", "with_smote", "metadata.json"),
}

for name, path in models.items():
    with open(path) as f:
        m = json.load(f)
    print(f"\n=== {name} ===")
    print(m["classification_report"])
