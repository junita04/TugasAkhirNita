"""
CLI: training + evaluasi + model registry Gaussian Naive Bayes.

    python scripts/train_model.py
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train + evaluate + registry Gaussian Naive Bayes"
    )
    args = parser.parse_args()

    from backend.ml.train import train_model
    from backend.ml.evaluate import evaluate_model
    from backend.ml.registry import save_model

    training_result = train_model()
    evaluation_result = evaluate_model(training_result)
    registry_result = save_model(evaluation_result)

    print("=" * 60)
    print("HASIL TRAINING")
    print("=" * 60)
    print(f"Rows Total   : {training_result['total_rows']}")
    print(f"Rows Train   : {training_result['train_count']}")
    print(f"Rows Test    : {training_result['test_count']}")
    print(f"Accuracy     : {evaluation_result['accuracy']:.4f}")
    print(f"Precision    : {evaluation_result['precision']:.4f}")
    print(f"Recall       : {evaluation_result['recall']:.4f}")
    print(f"F1 Score     : {evaluation_result['f1_score']:.4f}")
    print(f"Label Order  : {registry_result.get('label_order')}")
    print(f"Model        : {registry_result['model_path']}")
    print(f"Feature Pipe : {registry_result['feature_pipeline_path']}")
    print(f"Metadata     : {registry_result['metadata_path']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
