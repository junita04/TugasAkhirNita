import numpy as np

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_validate,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    make_scorer,
)

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from backend.ml.data_preparation import (
    load_training_dataset,
    check_model_leakage,
    build_target_encoding,
    encode_target,
    numpy_X,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    IDENTIFIER_COLUMN,
    POSITIVE_CLASS,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE = 42
TEST_SIZE = 0.20
N_SPLITS = 10

# =====================================================
# Penelitian ini TIDAK memakai scaler (StandardScaler
# maupun scaler lainnya). Feature X mentah langsung
# dimasukkan ke Gaussian Naive Bayes.
# =====================================================
PREPROCESSING = []


def build_estimator(use_smote=False):
    """
    Membangun estimator model tanpa scaler.

    MODEL A (baseline)   : GaussianNB()
    MODEL B (pembanding) : SMOTE + GaussianNB

    SMOTE di-apply DI DALAM pipeline (imblearn) sehingga saat
    cross_validate/fit hanya oversample training fold, TIDAK menyentuh
    validation/test fold (mencegah data leakage).
    """

    if use_smote:
        return ImbPipeline([
            ("smote", SMOTE(random_state=RANDOM_STATE)),
            ("model", GaussianNB()),
        ])

    return GaussianNB()


def extract_model(estimator):
    """
    Mengambil estimator GaussianNB sebenarnya.

    - MODEL A : estimator langsung GaussianNB.
    - MODEL B : ImbPipeline -> estimator langkah "model".
    """
    if hasattr(estimator, "named_steps") and "model" in estimator.named_steps:
        return estimator.named_steps["model"]
    return estimator


def train_model(use_smote=False):
    """
    Alur Tahap 5 (revisi, tanpa StandardScaler):
      1. Load training dataset dari Feature Store + leakage check.
      2. train_test_split stratified (80/20, random_state=42).
      3. StratifiedKFold k=10 di data development (80%).
      4. Fit final estimator pada development set + evaluasi holdout 20%.
      5. Fit estimator final pada seluruh data LULUS.

    MODEL A : X -> GaussianNB
    MODEL B : X_train -> SMOTE -> GaussianNB (SMOTE hanya training fold)
    """

    variant = "with_smote" if use_smote else "without_smote"

    logger.info("=" * 60)
    logger.info(f"TRAINING GAUSSIAN NAIVE BAYES ({variant.upper()}) - Tahap 5 Rev")
    logger.info("=" * 60)

    # =====================================================
    # 1. Dataset + leakage check
    # =====================================================

    pdf = load_training_dataset()

    forbidden = check_model_leakage(pdf)
    logger.info(f"Leakage check         : forbidden={forbidden}")

    class_mapping = build_target_encoding(pdf)
    y = encode_target(pdf, class_mapping)
    X = numpy_X(pdf)

    positive_index = class_mapping[POSITIVE_CLASS]

    logger.info(f"X shape               : {X.shape}")
    logger.info(f"Y shape               : {y.shape}")
    logger.info(f"Jumlah feature        : {X.shape[1]}")
    logger.info(f"Positive class        : {POSITIVE_CLASS} (index {positive_index})")

    # =====================================================
    # 2. Split development (80%) / holdout test (20%)
    # =====================================================

    X_dev, X_test, y_dev, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    logger.info(f"Development (80%)     : {len(X_dev)} records")
    logger.info(f"Holdout test (20%)    : {len(X_test)} records")
    logger.info(
        f"Distribusi class dev   : "
        f"{POSITIVE_CLASS}={int((y_dev == positive_index).sum())}, "
        f"Terlambat={int((y_dev != positive_index).sum())}"
    )

    # =====================================================
    # 3. 10-Fold Cross Validation (data development only)
    # =====================================================

    estimator = build_estimator(use_smote=use_smote)

    scoring = {
        "accuracy": make_scorer(accuracy_score),
        "precision": make_scorer(
            precision_score, pos_label=positive_index
        ),
        "recall": make_scorer(
            recall_score, pos_label=positive_index
        ),
        "f1": make_scorer(
            f1_score, pos_label=positive_index
        ),
    }

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    logger.info(
        f"Cross Validation       : StratifiedKFold k={N_SPLITS} "
        f"(shuffle=True, random_state={RANDOM_STATE})"
    )

    cv_results = cross_validate(
        estimator,
        X_dev,
        y_dev,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
    )

    folds_accuracy = cv_results["test_accuracy"]
    folds_precision = cv_results["test_precision"]
    folds_recall = cv_results["test_recall"]
    folds_f1 = cv_results["test_f1"]

    logger.info("=" * 60)
    logger.info("HASIL PER-FOLD (10-FOLD CV)")
    logger.info("=" * 60)
    for fold in range(N_SPLITS):
        logger.info(
            f"Fold {fold + 1:>2}: acc={folds_accuracy[fold]:.4f} "
            f"prec={folds_precision[fold]:.4f} "
            f"rec={folds_recall[fold]:.4f} f1={folds_f1[fold]:.4f}"
        )

    cv_summary = {
        "accuracy": {
            "mean": float(folds_accuracy.mean()),
            "std": float(folds_accuracy.std()),
        },
        "precision": {
            "mean": float(folds_precision.mean()),
            "std": float(folds_precision.std()),
        },
        "recall": {
            "mean": float(folds_recall.mean()),
            "std": float(folds_recall.std()),
        },
        "f1": {
            "mean": float(folds_f1.mean()),
            "std": float(folds_f1.std()),
        },
        "per_fold": {
            "accuracy": [float(v) for v in folds_accuracy],
            "precision": [float(v) for v in folds_precision],
            "recall": [float(v) for v in folds_recall],
            "f1": [float(v) for v in folds_f1],
        },
    }

    logger.info("=" * 60)
    for metric in ("accuracy", "precision", "recall", "f1"):
        logger.info(
            f"{metric.capitalize():<10}: mean={cv_summary[metric]['mean']:.4f} "
            f"std={cv_summary[metric]['std']:.4f}"
        )

    # =====================================================
    # 4. Final estimator pada development set + holdout test
    # =====================================================

    final_dev = build_estimator(use_smote=use_smote)
    final_dev.fit(X_dev, y_dev)

    y_pred = final_dev.predict(X_test)

    holdout = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(
            precision_score(y_test, y_pred, pos_label=positive_index)
        ),
        "recall": float(
            recall_score(y_test, y_pred, pos_label=positive_index)
        ),
        "f1": float(
            f1_score(y_test, y_pred, pos_label=positive_index)
        ),
        "confusion_matrix": confusion_matrix(
            y_test, y_pred, labels=[0, 1]
        ).tolist(),
        "classification_report": classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["Tepat Waktu", "Terlambat"],
            digits=4,
            zero_division=0,
        ),
    }

    logger.info("=" * 60)
    logger.info("HASIL HOLDOUT TEST (20%)")
    logger.info("=" * 60)
    for metric in ("accuracy", "precision", "recall", "f1"):
        logger.info(f"{metric.capitalize():<10}: {holdout[metric]:.4f}")
    logger.info("Confusion Matrix (rows=actual, cols=predicted):")
    logger.info("  [[TN, FP], [FN, TP]] (label: 0=Tepat Waktu, 1=Terlambat)")
    logger.info(f"  {holdout['confusion_matrix']}")

    # =====================================================
    # 5. Estimator final seluruh data LULUS
    # =====================================================

    final_full = build_estimator(use_smote=use_smote)
    final_full.fit(X, y)

    logger.info(f"Estimator final di-fit pada seluruh {len(X)} data LULUS.")

    # =====================================================
    # Return ringkasan (tanpa menyimpan ke registry di sini)
    # =====================================================

    return {
        "class_mapping": class_mapping,
        "positive_class": POSITIVE_CLASS,
        "positive_index": positive_index,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "identifier_column": IDENTIFIER_COLUMN,
        "n_records": int(len(X)),
        "class_distribution": {
            label: int((y == index).sum())
            for label, index in class_mapping.items()
        },
        "n_features": int(X.shape[1]),
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "dev_size": int(len(X_dev)),
        "test_size_records": int(len(X_test)),
        "cv": {
            "algorithm": "StratifiedKFold",
            "n_splits": N_SPLITS,
            "shuffle": True,
            "random_state": RANDOM_STATE,
        },
        "preprocessing": PREPROCESSING,
        "cv_summary": cv_summary,
        "holdout": holdout,
        "pipeline_dev": final_dev,
        "pipeline_full": final_full,
        "X_test": X_test,
        "y_test": y_test,
        "forbidden_features": forbidden,
        "use_smote": use_smote,
        "variant": variant,
    }