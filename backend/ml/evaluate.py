import numpy as np

from sklearn.naive_bayes import GaussianNB

from backend.ml.train import extract_model
from backend.ml.registry import (
    save_model,
    load_model,
    MODEL_NAME,
    MODEL_VERSION,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _print_report(result, registry_info):
    """Mencetak laporan akhir untuk satu varian Tahap 3 (dataset baru)."""

    variant = result["variant"]

    print()
    print("=" * 88)
    print(f"LAPORAN TAHAP 3 - {variant.upper()}")
    print("=" * 88)

    print("# A. DATASET")
    print(f"  Source          : local.feature_store.training_dataset")
    print(f"  Jumlah data     : {result['n_records']}")
    print(f"  Jumlah feature  : {result['n_features']}")
    print(f"  Jumlah target   : 1 ({result['target_column']})")
    print(f"  Jumlah kelas    : {len(result['class_mapping'])}")
    print(f"  Distribusi kelas: {result['class_distribution']}")

    print()
    print("# B. FEATURE")
    print(f"  X: {result['feature_columns']}")
    print(f"  Y: {result['target_column']}")

    print()
    print("# C. SPLIT")
    print(f"  Training/development : 80% ({result['dev_size']} records)")
    print(f"  Holdout test         : 20% ({result['test_size_records']} records)")
    print(f"  random_state={result['random_state']}, stratify=y")

    print()
    print("# D. K-FOLD (StratifiedKFold k=10)")
    per_fold = result["cv_summary"]["per_fold"]
    print(f"  Algorithm: {result['cv']['algorithm']}, K={result['cv']['n_splits']}")
    for fold in range(10):
        print(
            f"  Fold {fold + 1:>2}: acc={per_fold['accuracy'][fold]:.4f} "
            f"prec={per_fold['precision'][fold]:.4f} "
            f"rec={per_fold['recall'][fold]:.4f} f1={per_fold['f1'][fold]:.4f}"
        )
    print()
    for metric in ("accuracy", "precision", "recall", "f1"):
        m = result["cv_summary"][metric]
        print(f"  {metric.capitalize():<10}: mean={m['mean']:.4f} std={m['std']:.4f}")

    print()
    print("# E. HOLDOUT TEST")
    h = result["holdout"]
    print(f"  Accuracy : {h['accuracy']:.4f}")
    print(f"  Precision: {h['precision']:.4f}")
    print(f"  Recall   : {h['recall']:.4f}")
    print(f"  F1       : {h['f1']:.4f}")
    print(f"  Confusion Matrix (rows=actual: 0=Tepat Waktu,1=Terlambat; cols=predicted):")
    print(f"    {h['confusion_matrix']}")

    print()
    print("# F. LEAKAGE CHECK")
    print(f"  Forbidden features detected = {len(result['forbidden_features'])}")
    print(f"  Result: {'PASS' if not result['forbidden_features'] else 'FAIL'}")

    print()
    print("# G. MODEL")
    print(f"  Model        : {MODEL_NAME}")
    print(f"  Version      : {MODEL_VERSION}")
    print(f"  Variant      : {variant}")
    print(f"  Type         : GaussianNB")
    print(f"  Sampling     : {'SMOTE' if result['use_smote'] else 'none'}")
    print(f"  Preprocessing: {'none (tanpa scaler)' if not result['preprocessing'] else result['preprocessing']}")
    print(f"  Feature order: {result['feature_columns']}")
    print(f"  Class mapping: {result['class_mapping']}")
    print(f"  Artifact path: {registry_info['artifact_path']}")

    print("=" * 88)


def _quality_gates(result, registry_info, pipeline, smoke_ok, feature_order_ok):
    """Quality gate untuk satu varian."""

    return [
        ("training dataset terbaca", result["n_records"] > 0),
        ("X schema benar", feature_order_ok),
        ("Y schema benar", result["target_column"] == "label"),
        ("no leakage", not result["forbidden_features"]),
        ("train/test split benar", result["test_size"] == 0.20),
        (
            "StratifiedKFold k=10 berjalan",
            len(result["cv_summary"]["per_fold"]["accuracy"]) == 10,
        ),
        ("metrics CV tersedia", all(
            k in result["cv_summary"] for k in ("accuracy", "precision", "recall", "f1")
        )),
        ("holdout test selesai", result["holdout"]["accuracy"] is not None),
        ("confusion matrix tersedia", bool(result["holdout"]["confusion_matrix"])),
        ("final model berhasil dibuat", result["pipeline_full"] is not None),
        ("model artifact berhasil disimpan", bool(registry_info["artifact_path"])),
        ("model artifact berhasil di-load", pipeline is not None),
        ("smoke test berhasil", smoke_ok),
        ("tanpa StandardScaler", not result["preprocessing"]),
    ]


def _smoke_test(pipeline, result):
    """Prediksi sampel kecil dari X_test untuk memastikan pipeline jalan."""

    smoke_X = result["X_test"][:5]
    smoke_pred_int = pipeline.predict(smoke_X)

    inverse_mapping = {v: k for k, v in result["class_mapping"].items()}
    smoke_pred_label = [inverse_mapping[int(idx)] for idx in smoke_pred_int]

    valid_labels = set(result["class_mapping"].keys())
    smoke_ok = all(label in valid_labels for label in smoke_pred_label)

    return smoke_ok, smoke_X, smoke_pred_label


def _run_variant(use_smote):
    """Train + save + load + validate satu varian."""

    from backend.ml.train import train_model

    variant = "with_smote" if use_smote else "without_smote"

    result = train_model(use_smote=use_smote)
    registry_info = save_model(result)

    pipeline, _metadata = load_model(use_smote=use_smote)

    logger.info("=" * 60)
    logger.info(f"VALIDASI MODEL ARTIFACT ({variant.upper()})")
    logger.info("=" * 60)

    model_type_ok = isinstance(extract_model(pipeline), GaussianNB)
    logger.info(f"Model type = GaussianNB      : {'PASS' if model_type_ok else 'FAIL'}")

    feature_order_ok = _metadata["feature_names"] == result["feature_columns"]
    logger.info(f"Feature schema              : {'PASS' if feature_order_ok else 'FAIL'}")

    no_scaler_ok = not _metadata.get("has_scaler", True)
    logger.info(f"Tanpa StandardScaler        : {'PASS' if no_scaler_ok else 'FAIL'}")

    if use_smote:
        has_smote = hasattr(pipeline, "named_steps") and "smote" in pipeline.named_steps
        logger.info(f"SMOTE di pipeline           : {'PASS' if has_smote else 'FAIL'}")

    smoke_ok, smoke_X, smoke_pred_label = _smoke_test(pipeline, result)

    print()
    print("# H. MODEL LOAD TEST")
    print(f"  Model reload         : {'PASS' if model_type_ok else 'FAIL'}")
    print(f"  Prediction smoke test: {'PASS' if smoke_ok else 'FAIL'}")
    if smoke_ok:
        print("  Smoke sample (X -> prediksi):")
        for row, label in zip(smoke_X, smoke_pred_label):
            print(f"    {list(np.round(row, 2))} -> {label}")
    print("=" * 88)

    gates = _quality_gates(
        result, registry_info, pipeline, smoke_ok, feature_order_ok
    )

    print()
    print(f"QUALITY GATE ({variant})")
    all_pass = True
    for label, passed in gates:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
        all_pass = all_pass and passed

    status = "SUCCESS" if all_pass else "FAILED"
    print()
    print(f"VARIANT {variant.upper()} STATUS: {status}")

    return {
        "variant": variant,
        "status": status,
        "quality_gates": dict(gates),
        "registry_info": registry_info,
        "result": result,
        "no_scaler": no_scaler_ok,
        "model_type": model_type_ok,
    }


def run_ml_pipeline():
    """
    Orkestrator Tahap 3: melatih DUA varian GaussianNB.

      (1) without_smote (baseline)
      (2) with_smote    (SMOTE di training fold guna menangani imbalance)

    Setiap varian: training (10-fold CV) -> holdout test -> save registry
    -> load -> validasi artifact -> smoke test. Kemudian dibandingkan.

    TIDAK menyentuh inference_dataset, prediction, dan layanan lain.
    """

    logger.info("=" * 60)
    logger.info("MEMULAI ML PIPELINE (Tahap 3) - DUA VARIAN")
    logger.info("=" * 60)

    a = _run_variant(use_smote=False)
    b = _run_variant(use_smote=True)

    # =====================================================
    # Perbandingan dua varian
    # =====================================================

    ra = a["result"]
    rb = b["result"]

    print()
    print("=" * 88)
    print("PERBANDINGAN VARIAN - TAHAP 3")
    print("=" * 88)

    headers = ["metric", "without_smote", "with_smote", "pemenang"]
    rows = []

    for metric in ("accuracy", "precision", "recall", "f1"):
        m = "F1" if metric == "f1" else metric.capitalize()
        va = ra["holdout"][metric]
        vb = rb["holdout"][metric]
        winner = "without_smote" if va > vb else ("with_smote" if vb > va else "seri")
        rows.append((m, f"{va:.4f}", f"{vb:.4f}", winner))

    print("Holdout metrics:")
    print(f"  {'metric':<12}{'without_smote':<16}{'with_smote':<14}pemenang")
    for name, s_a, s_b, winner in rows:
        print(f"  {name:<12}{s_a:<16}{s_b:<14}{winner}")

    print()
    print("CV summary (mean):")
    for metric in ("accuracy", "precision", "recall", "f1"):
        m = "F1" if metric == "f1" else metric.capitalize()
        ma = ra["cv_summary"][metric]["mean"]
        mb = rb["cv_summary"][metric]["mean"]
        winner = "without_smote" if ma > mb else ("with_smote" if mb > ma else "seri")
        print(f"  {m:<12}{ma:.4f} vs {mb:.4f}  -> {winner}")

    print("=" * 88)

    return {
        "without_smote": a,
        "with_smote": b,
        "overall": "SUCCESS" if (
            a["status"] == "SUCCESS" and b["status"] == "SUCCESS"
        ) else "FAILED",
    }