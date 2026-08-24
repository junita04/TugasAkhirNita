"""
Tahap 6 — Inference / Prediction Pipeline (VERSI PARQUET).

Membaca inference dataset (mahasiswa AKTIF) dari Feature Store, memuat KEDUA
model final revisi Tahap 3 dari Model Registry (v3.0.0, TANPA StandardScaler):

  * MODEL A (without_smote): GaussianNB()
  * MODEL B (with_smote)   : SMOTE + GaussianNB (imblearn pipeline)

Kedua model melakukan prediksi pada inference dataset yang SAMA, lalu hasilnya
disimpan sebagai FILE PARQUET BIASA (bukan Iceberg):

  * data/predictions/prediction_result_without_smote.parquet
  * data/predictions/prediction_result_with_smote.parquet
  * data/predictions/prediction_comparison.parquet (opsional, untuk analisis)

Serta disusun perbandingan agreement/disagreement antar kedua model dan
quality report ``logs/inference_quality_report.json``.

TIDAK melakukan retraining, K-Fold, SMOTE, fit ulang scaler, maupun
penulisan metadata Iceberg untuk output prediction.
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, LOG_DIR, PROJECT_ROOT
from backend.utils.logger import get_logger

from backend.feature_store.feature_engineering import (
    FEATURE_X,
    FORBIDDEN_FEATURES,
)
from backend.ml.registry import load_model, MODEL_VERSION, MODEL_NAME

logger = get_logger(__name__)

INFERENCE_TABLE = f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset"

PREDICTION_DIR = PROJECT_ROOT / "data" / "predictions"

PARQUET_WITHOUT_SMOTE = PREDICTION_DIR / "prediction_result_without_smote.parquet"
PARQUET_WITH_SMOTE = PREDICTION_DIR / "prediction_result_with_smote.parquet"
PARQUET_COMPARISON = PREDICTION_DIR / "prediction_comparison.parquet"

IDENTIFIER_COLUMN = "id_mahasiswa"
PREDICTION_LABEL_COLUMN = "prediksi_status_kelulusan"
PREDICTION_TIMESTAMP_COLUMN = "prediction_timestamp"
MODEL_VERSION_COLUMN = "model_version"
MODEL_VARIANT_COLUMN = "model_variant"
PREDICTION_PROBABILITY_COLUMN = "probabilitas_prediksi"

INFERENCE_FEATURES = FEATURE_X  # ["ip", "sks", "angkatan", "jumlah_mk"]

VARIANT_WITHOUT_SMOTE = "without_smote"
VARIANT_WITH_SMOTE = "with_smote"

VARIANTS = [
    {
        "use_smote": False,
        "variant": VARIANT_WITHOUT_SMOTE,
        "parquet": PARQUET_WITHOUT_SMOTE,
        "display": "WITHOUT_SMOTE",
    },
    {
        "use_smote": True,
        "variant": VARIANT_WITH_SMOTE,
        "parquet": PARQUET_WITH_SMOTE,
        "display": "WITH_SMOTE",
    },
]


class InferenceError(RuntimeError):
    """Error spesifik pipeline inference (schema/leakage/validasi)."""


def load_inference_dataset(spark):
    """
    Membaca inference dataset dari Feature Store sebagai pandas DataFrame.

    Inference dataset (Tahap 4) sudah bersih: hanya kolom id_mahasiswa
    + FEATURE_X, tidak ada NULL pada fitur wajib, tidak ada duplikat id
    (grain 1 baris = 1 mahasiswa AKTIF).
    """

    logger.info("=" * 60)
    logger.info("MEMBACA INFERENCE DATASET (FEATURE STORE)")
    logger.info("=" * 60)

    df = spark.table(INFERENCE_TABLE)

    logger.info(f"Kolom        : {sorted(df.columns)}")
    logger.info(f"Rows         : {df.count()}")

    pdf = df.toPandas()

    return pdf


def validate_schema(pdf):
    """
    Validasi schema inference sebelum prediksi.

    - Seluruh feature tersedia dan tepat berjumlah 4.
    - Tidak ada kolom tambahan di luar id + feature (leakage check).
    - Tidak ada NULL pada feature maupun id.
    - id_mahasiswa tidak duplikat.

    Jika gagal -> InferenceError (pipeline dihentikan).
    """

    logger.info("=" * 60)
    logger.info("VALIDASI SCHEMA INFERENCE")
    logger.info("=" * 60)

    # 1. Seluruh feature tersedia
    missing = [c for c in INFERENCE_FEATURES if c not in pdf.columns]
    if missing:
        raise InferenceError(
            f"Feature wajib tidak ditemukan pada inference dataset: {missing}"
        )

    # 2. Tidak ada kolom tambahan (leakage)
    allowed = set(INFERENCE_FEATURES) | {IDENTIFIER_COLUMN}
    extra = [c for c in pdf.columns if c not in allowed]
    if extra:
        raise InferenceError(
            "DATA LEAKAGE DETECTED: kolom di luar id+feature pada inference "
            f"dataset: {extra}. Pipeline dihentikan."
        )

    # 3. Jumlah feature = 4
    n_features = len(INFERENCE_FEATURES)
    if n_features != 4:
        raise InferenceError(f"Jumlah feature tidak sesuai (harus 4): {n_features}")

    # 4. NULL check pada feature
    null_features = {
        column: int(pdf[column].isnull().sum())
        for column in INFERENCE_FEATURES
    }
    if any(null_features.values()):
        raise InferenceError(
            f"NULL terdeteksi pada feature inference: {null_features}"
        )

    # 5. NULL check pada id
    null_id = int(pdf[IDENTIFIER_COLUMN].isnull().sum())
    if null_id != 0:
        raise InferenceError(
            f"NULL terdeteksi pada {IDENTIFIER_COLUMN}: {null_id}"
        )

    # 6. Duplikat id
    duplicate_id = int(pdf[IDENTIFIER_COLUMN].duplicated().sum())
    if duplicate_id != 0:
        raise InferenceError(
            f"Duplikat {IDENTIFIER_COLUMN} terdeteksi: {duplicate_id}"
        )

    total = len(pdf)
    distinct_id = int(pdf[IDENTIFIER_COLUMN].nunique())
    logger.info(f"Total rows           : {total}")
    logger.info(f"Distinct id          : {distinct_id}")
    logger.info(f"Jumlah feature       : {n_features}")
    logger.info(f"Null feature         : {null_features}")
    logger.info(f"Null id              : {null_id}")
    logger.info(f"Duplicate id         : {duplicate_id}")
    logger.info(
        f"Grain 1 baris = 1 mhs : {'PASS' if total == distinct_id else 'FAIL'}"
    )

    if total != distinct_id:
        raise InferenceError(
            "Grain inference tidak 1 baris per mahasiswa: "
            f"total={total}, distinct={distinct_id}"
        )

    return {
        "total_rows": total,
        "distinct_id": distinct_id,
        "n_features": n_features,
        "null_features": null_features,
        "null_id": null_id,
        "duplicate_id": duplicate_id,
        "feature_order": list(INFERENCE_FEATURES),
    }


def load_final_model(use_smote):
    """
    Memuat model final revisi Tahap 3 (v3.0.0) dari Model Registry.

    Memakai metadata untuk memvalidasi konsistensi feature training dan
    memastikan StandardScaler TIDAK ada.
    """

    variant = "with_smote" if use_smote else "without_smote"

    logger.info("=" * 60)
    logger.info(f"MEMUAT MODEL FINAL ({variant.upper()})")
    logger.info("=" * 60)

    pipeline, metadata = load_model(use_smote=use_smote)

    logger.info(f"Artifact        : {metadata.get('artifact_path')}")
    logger.info(f"Model name      : {metadata.get('model_name')}")
    logger.info(f"Model version   : {metadata.get('model_version')}")
    logger.info(f"Variant         : {metadata.get('variant')}")
    logger.info(f"Type            : {metadata.get('model_type')}")
    logger.info(f"Feature names   : {metadata.get('feature_names')}")
    logger.info(f"Preprocessing   : {metadata.get('preprocessing')}")
    logger.info(f"Has scaler      : {metadata.get('has_scaler')}")
    logger.info(f"Class mapping   : {metadata.get('class_mapping')}")

    training_features = metadata.get("feature_names") or []

    if training_features != INFERENCE_FEATURES:
        raise InferenceError(
            "MISMATCH feature: training artifact memakai "
            f"{training_features} tetapi inference memakai {INFERENCE_FEATURES}. "
            "Gunakan artifact model revisi Tahap 3 (v3.0.0)."
        )

    if metadata.get("has_scaler", True):
        raise InferenceError(
            "Artifact masih memakai StandardScaler (v1). Gunakan artifact "
            "revisi Tahap 3 (v3.0.0) tanpa scaler."
        )

    logger.info(
        "Feature inference konsisten dengan feature training revisi Tahap 3: "
        f"{INFERENCE_FEATURES}"
    )

    return pipeline, metadata


def build_X(pdf):
    """
    Membangun matriks X dari fitur inference.

    urutan kolom persis mengikuti INFERENCE_FEATURES agar konsisten
    dengan urutan feature saat training.
    """
    X = pdf[INFERENCE_FEATURES].astype(float).to_numpy()
    return X


def predict_inference(pdf, pipeline):
    """
    Melakukan prediksi pada seluruh mahasiswa inference.

    Output prediksi (integer index) dipetakan kembali ke label
    menggunakan mapping yang TERSIMPAN pada metadata training
    (bukan urutan ulang). Mapping tidak dibalik.
    """

    logger.info("=" * 60)
    logger.info("PREDIKSI INFERENCE")
    logger.info("=" * 60)

    X = build_X(pdf)

    y_pred = pipeline.predict(X)

    if hasattr(pipeline, "predict_proba"):
        y_proba = pipeline.predict_proba(X)
    else:
        y_proba = None

    logger.info(f"Shape X          : {X.shape}")
    logger.info(f"Jumlah prediksi  : {len(y_pred)}")
    logger.info(f"predict_proba    : {'ada' if y_proba is not None else 'tidak (dokumentasi)'}")

    return X, y_pred, y_proba


def build_prediction_result(pdf, y_pred, y_proba, metadata, variant):
    """
    Menyusun tabel hasil prediksi.

    Kolom:
      - id_mahasiswa            (identifier)
      - ip, sks, angkatan, jumlah_mk  (feature, urutan training)
      - prediksi_status_kelulusan     (label: "Tepat Waktu" / "Terlambat")
      - probabilitas_prediksi         (probabilitas kelas yang diprediksi)
      - prediction_timestamp
      - model_version
      - model_variant

    Tidak ada feature training lama (lama_studi, ipk, total_sks, dll).
    """

    logger.info("=" * 60)
    logger.info(f"MENYUSUN PREDICTION RESULT ({variant.upper()})")
    logger.info("=" * 60)

    class_mapping = metadata.get("class_mapping") or {}
    index_to_label = {int(v): k for k, v in class_mapping.items()}

    labels = [index_to_label[int(idx)] for idx in y_pred]

    valid_labels = set(class_mapping.keys())
    invalid = [lab for lab in labels if lab not in valid_labels]
    if invalid:
        raise InferenceError(
            f"Label prediksi tidak dikenal: {set(invalid)}. Mapping salah?"
        )

    # Probabilitas kelas yang diprediksi (opsional, dari predict_proba)
    proba_pred = None
    if y_proba is not None:
        proba_pred = np.array(
            [float(proba[int(idx)]) for proba, idx in zip(y_proba, y_pred)]
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result_pdf = pd.DataFrame({
        IDENTIFIER_COLUMN: pdf[IDENTIFIER_COLUMN].values,
        "ip": pdf["ip"].values,
        "sks": pdf["sks"].values,
        "angkatan": pdf["angkatan"].values,
        "jumlah_mk": pdf["jumlah_mk"].values,
        PREDICTION_LABEL_COLUMN: labels,
        PREDICTION_PROBABILITY_COLUMN: proba_pred if proba_pred is not None
        else np.full(len(y_pred), np.nan),
        PREDICTION_TIMESTAMP_COLUMN: timestamp,
        MODEL_VERSION_COLUMN: MODEL_VERSION,
        MODEL_VARIANT_COLUMN: variant,
    })

    logger.info(f"Jumlah baris hasil : {len(result_pdf)}")
    if proba_pred is not None:
        logger.info(f"Probabilitas      : [min={proba_pred.min():.4f}, "
                    f"max={proba_pred.max():.4f}, mean={proba_pred.mean():.4f}]")

    return result_pdf, index_to_label


def save_prediction_parquet(result_pdf, variant, path):
    """
    Menyimpan prediction result sebagai PARQUET BIASA (bukan Iceberg).
    """

    logger.info("=" * 60)
    logger.info(f"MENYIMPAN PREDICTION RESULT (PARQUET) -> {path}")
    logger.info("=" * 60)

    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)

    result_pdf.to_parquet(path, index=False)

    logger.info(f"✓ Parquet tersimpan ({len(result_pdf)} rows): {path}")

    return path


def validate_parquet(spark, path, expected_count, variant):
    """
    Quality gate file Parquet hasil prediksi.

    A. Row count        : jumlah inference input == jumlah prediction result
    B. Unique ID        : count(distinct id) == jumlah row
    C. NULL             : tidak ada NULL pada seluruh kolom wajib
    D. Distribusi       : jumlah + persentase tiap label
    E. Coverage         : seluruh mahasiswa AKTIF punya tepat satu prediksi
    F. Schema           : tidak ada feature training lama di prediction result
    G. Grain            : 1 baris = 1 mahasiswa (no row multiplication)
    """

    logger.info("=" * 60)
    logger.info(f"VALIDASI OUTPUT ({variant.upper()}) — QUALITY GATE")
    logger.info("=" * 60)

    pdf = pd.read_parquet(path)

    total = len(pdf)
    distinct_id = int(pdf[IDENTIFIER_COLUMN].nunique())

    # =====================================================
    # F. Schema: tidak boleh ada feature training lama
    # =====================================================

    legacy_features = [
        c for c in pdf.columns
        if c in FORBIDDEN_FEATURES or c in {
            "lama_studi", "tanggal_keluar", "ipk", "total_sks",
            "status_mahasiswa", "status_kelulusan",
            "estimasi_semester", "persentase_sks",
        }
    ]

    # =====================================================
    # C. NULL check
    # =====================================================

    required_columns = [
        IDENTIFIER_COLUMN, "ip", "sks", "angkatan", "jumlah_mk",
        PREDICTION_LABEL_COLUMN, MODEL_VARIANT_COLUMN,
    ]

    null_counts = {
        column: int(pdf[column].isnull().sum())
        for column in required_columns
    }

    # =====================================================
    # D. Distribusi
    # =====================================================

    distribution = pdf[PREDICTION_LABEL_COLUMN].value_counts().to_dict()
    distribution = {k: int(v) for k, v in distribution.items()}

    # =====================================================
    # Hasil
    # =====================================================

    total_null = sum(null_counts.values())

    result = {
        "variant": variant,
        "file": str(path),
        "source_table": INFERENCE_TABLE,
        "input_count": expected_count,
        "prediction_count": total,
        "distinct_id": distinct_id,
        "row_count_ok": total == expected_count,
        "unique_id_ok": distinct_id == total,
        "null_counts": null_counts,
        "total_null": total_null,
        "null_ok": total_null == 0,
        "distribution": distribution,
        "coverage": {
            "covered": total,
            "expected": expected_count,
            "ok": total == expected_count and distinct_id == expected_count,
        },
        "legacy_features_found": legacy_features,
        "legacy_schema_ok": len(legacy_features) == 0,
        "grain": {
            "rows": total,
            "distinct_id": distinct_id,
            "ok": total == distinct_id,
        },
    }

    for label, count in sorted(distribution.items()):
        pct = (count / total) * 100 if total else 0
        logger.info(f"  {label:<14}: {count:>7}  ({pct:.2f}%)")

    logger.info(f"Prediction count : {total} (input {expected_count})")
    logger.info(f"Distinct id      : {distinct_id}")
    logger.info(f"Null total       : {total_null}")
    logger.info(f"Legacy features  : {legacy_features}")

    return result


def compare_models():
    """
    Perbandingan agreement/disagreement antar kedua model
    (without_smote vs with_smote) per id_mahasiswa.
    """

    logger.info("=" * 60)
    logger.info("PERBANDINGAN AGREE / DISAGREE ANTAR MODEL")
    logger.info("=" * 60)

    a = pd.read_parquet(PARQUET_WITHOUT_SMOTE)[
        [IDENTIFIER_COLUMN, PREDICTION_LABEL_COLUMN]
    ].rename(columns={PREDICTION_LABEL_COLUMN: "prediksi_a"})
    b = pd.read_parquet(PARQUET_WITH_SMOTE)[
        [IDENTIFIER_COLUMN, PREDICTION_LABEL_COLUMN]
    ].rename(columns={PREDICTION_LABEL_COLUMN: "prediksi_b"})

    merged = a.merge(b, on=IDENTIFIER_COLUMN, how="inner")

    total = len(merged)
    agreement = int((merged["prediksi_a"] == merged["prediksi_b"]).sum())
    disagreement = total - agreement
    agreement_rate = (agreement / total) * 100 if total else 0

    mismatch_rows = merged[merged["prediksi_a"] != merged["prediksi_b"]]
    mismatch_pattern = mismatch_rows.groupby(
        ["prediksi_a", "prediksi_b"]
    ).size().to_dict()

    logger.info(f"Total id bersama : {total}")
    logger.info(f"Agree            : {agreement} ({agreement_rate:.2f}%)")
    logger.info(f"Disagree         : {disagreement} ({100 - agreement_rate:.2f}%)")
    for (pa, pb), n in sorted(mismatch_pattern.items()):
        logger.info(f"  {pa} -> {pb}: {n}")

    return {
        "total": total,
        "agreement": agreement,
        "disagreement": disagreement,
        "agreement_rate": round(agreement_rate, 4),
        "disagreement_rate": round(100 - agreement_rate, 4),
        "mismatch_pattern": {f"{pa} -> {pb}": int(n) for (pa, pb), n in mismatch_pattern.items()},
        "sample_disagree_ids": mismatch_rows[IDENTIFIER_COLUMN].head(10).tolist(),
    }


def run_inference(smoke_test=False, limit=None):
    """
    Orkestrator Tahap 6 (versi Parquet):
      load inference dataset
      -> validasi schema
      -> untuk tiap varian: load model v3.0.0 -> prediksi -> simpan
         Parquet biasa -> quality gate output
      -> perbandingan agreement/disagreement antar model
      -> tulis quality report

    smoke_test=True memproses subset (limit baris) UNTUK VERIFIKASI SAJA
    tanpa menyimpan file final. Setelah smoke test sukses, jalankan penuh
    dengan smoke_test=False.
    """

    logger.info("=" * 60)
    logger.info("TAHAP 6 — INFERENCE / PREDICTION (VERSI PARQUET)")
    logger.info("=" * 60)

    spark = get_spark("TugasAkhirNita - Inference")

    # 1. Baca inference dataset
    pdf = load_inference_dataset(spark)

    # 2. Validasi schema
    schema_report = validate_schema(pdf)

    # =========================================================
    # Mode smoke test: hanya subset, tidak menyimpan file final
    # =========================================================

    if smoke_test:
        if limit is None or limit <= 0:
            limit = 5
        pdf = pdf.head(limit)

        for variant_def in VARIANTS:
            pipeline, metadata = load_final_model(
                use_smote=variant_def["use_smote"]
            )
            X, y_pred, y_proba = predict_inference(pdf, pipeline)
            result_pdf, _ = build_prediction_result(
                pdf, y_pred, y_proba, metadata, variant_def["variant"]
            )
            logger.info(
                f"SMOKE TEST PASS [{variant_def['variant']}]: "
                f"{len(result_pdf)} rows, label={sorted(result_pdf[PREDICTION_LABEL_COLUMN].unique())}"
            )

        logger.info("SMOKE TEST SELESAI — jalankan penuh inference dataset.")
        return {"smoke_test": True, "schema_validation": schema_report,
                "status": "SMOKE_TEST_PASS"}

    # =========================================================
    # Mode penuh: prediksi dua varian dan simpan Parquet
    # =========================================================

    per_variant_reports = {}

    for variant_def in VARIANTS:
        use_smote = variant_def["use_smote"]
        variant = variant_def["variant"]
        path = variant_def["parquet"]

        pipeline, metadata = load_final_model(use_smote=use_smote)

        X, y_pred, y_proba = predict_inference(pdf, pipeline)

        result_pdf, index_to_label = build_prediction_result(
            pdf, y_pred, y_proba, metadata, variant
        )

        save_prediction_parquet(result_pdf, variant, path)

        output_report = validate_parquet(
            spark, path, expected_count=len(pdf), variant=variant
        )

        per_variant_reports[variant] = {
            "model": {
                "name": MODEL_NAME,
                "version": MODEL_VERSION,
                "variant": variant,
                "use_smote": use_smote,
                "artifact_path": metadata.get("artifact_path"),
                "model_type": metadata.get("model_type"),
                "preprocessing": metadata.get("preprocessing"),
                "has_scaler": metadata.get("has_scaler"),
                "class_mapping": metadata.get("class_mapping"),
            },
            "prediction": {
                "X_shape": [int(v) for v in X.shape],
                "n_prediction": int(len(y_pred)),
                "predict_proba": y_proba is not None,
            },
            "output_validation": output_report,
            "output_parquet": str(path),
        }

    # 4. Perbandingan agreement/disagreement
    comparison = compare_models()

    # 5. Menyimpan dataframe comparison sebagai Parquet biasa (opsional)
    _save_comparison_parquet()

    # 6. Rangkuman report
    report = {
        "tahap": "TAHAP_6_INFERENCE_PARQUET",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "inference": {
            "table": INFERENCE_TABLE,
            "feature_x": INFERENCE_FEATURES,
            "forbidden_features": FORBIDDEN_FEATURES,
        },
        "schema_validation": schema_report,
        "variants": per_variant_reports,
        "comparison": comparison,
        "model_version": MODEL_VERSION,
        "status": "SUCCESS",
    }

    _write_quality_report(report)

    return report


def _save_comparison_parquet():
    """Menyimpan dataframe perbandingan prediksi dua model (Parquet biasa)."""

    logger.info("=" * 60)
    logger.info("SIMpan COMPARISON DATAFRAME (PARQUET)")
    logger.info("=" * 60)

    a = pd.read_parquet(PARQUET_WITHOUT_SMOTE)[
        [IDENTIFIER_COLUMN, PREDICTION_LABEL_COLUMN]
    ].rename(columns={PREDICTION_LABEL_COLUMN: "prediction_without_smote"})
    b = pd.read_parquet(PARQUET_WITH_SMOTE)[
        [IDENTIFIER_COLUMN, PREDICTION_LABEL_COLUMN]
    ].rename(columns={PREDICTION_LABEL_COLUMN: "prediction_with_smote"})

    merged = a.merge(b, on=IDENTIFIER_COLUMN, how="inner")

    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(PARQUET_COMPARISON, index=False)

    logger.info(f"✓ Comparison parquet tersimpan: {PARQUET_COMPARISON} "
                f"({len(merged)} rows)")


def _write_quality_report(report):
    """Menyimpan quality report khusus inference ke logs/."""

    path = LOG_DIR / "inference_quality_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Quality report tersimpan : {path}")


def print_report(report):
    """Mencetak laporan akhir Tahap 6."""

    print()
    print("=" * 88)
    print("TAHAP 6 — INFERENCE / PREDICTION (VERSI PARQUET)")
    print("=" * 88)

    if report.get("smoke_test"):
        print("# SMOKE TEST")
        print(f"  Status : {report['status']}")
        print("  Jalankan inference penuh setelah ini.")
        print("=" * 88)
        return

    inf = report["inference"]
    schema = report["schema_validation"]
    comparison = report["comparison"]

    print("# A. FILE YANG DIUBAH/DIBUAT")
    print("  - backend/ml/inference.py")
    print("  - data/predictions/prediction_result_without_smote.parquet")
    print("  - data/predictions/prediction_result_with_smote.parquet")
    print("  - data/predictions/prediction_comparison.parquet")
    print("  - logs/inference_quality_report.json")

    print()
    print("# B. MODEL ARTIFACT (v3.0.0, tanpa StandardScaler)")
    for variant, vr in report["variants"].items():
        m = vr["model"]
        print(f"  [{variant}]")
        print(f"    Model        : {m['name']} ({m['version']})")
        print(f"    Type         : {m['model_type']}")
        print(f"    Artifact path: {m['artifact_path']}")
        print(f"    Preprocess   : {m['preprocessing']} (has_scaler={m['has_scaler']})")
        print(f"    Class mapping: {m['class_mapping']}")

    print()
    print("# C. FEATURE YANG DIGUNAKAN")
    print(f"  X            : {inf['feature_x']}")
    print(f"  Jumlah       : {schema['n_features']}")

    print()
    print("# D. JUMLAH MAHASISWA INFERENCE")
    print(f"  Input        : {schema['total_rows']}")

    print()
    print("# E. JUMLAH PREDICTION")
    for variant, vr in report["variants"].items():
        out = vr["output_validation"]
        print(f"  [{variant}] Output : {out['prediction_count']} rows")

    print()
    print("# F. DISTRIBUSI PREDIKSI")
    for variant, vr in report["variants"].items():
        out = vr["output_validation"]
        print(f"  [{variant}]")
        for label, count in sorted(out["distribution"].items()):
            pct = (count / out["prediction_count"]) * 100
            print(f"    {label:<14}: {count}  ({pct:.2f}%)")

    print()
    print("# G. VALIDATION RESULT")
    for variant, vr in report["variants"].items():
        out = vr["output_validation"]
        print(f"  [{variant}]")
        print(f"    Row count match : {'PASS' if out['row_count_ok'] else 'FAIL'}")
        print(f"    Unique ID       : {'PASS' if out['unique_id_ok'] else 'FAIL'}")
        print(f"    NULL            : {'PASS' if out['null_ok'] else 'FAIL'}"
              f"  (null={out['total_null']})")
        print(f"    Coverage        : {out['coverage']['covered']} / {out['coverage']['expected']}"
              f"  {'PASS' if out['coverage']['ok'] else 'FAIL'}")
        print(f"    Grain           : {'PASS' if out['grain']['ok'] else 'FAIL'}")
        print(f"    Legacy features : {out['legacy_features_found']}"
              f"  {'PASS' if out['legacy_schema_ok'] else 'FAIL'}")

    print()
    print("# H. MODEL CONSISTENCY (agreement/disagreement)")
    print(f"  Total id dibanding     : {comparison['total']}")
    print(f"  Agree                  : {comparison['agreement']} ({comparison['agreement_rate']:.2f}%)")
    print(f"  Disagree               : {comparison['disagreement']} ({comparison['disagreement_rate']:.2f}%)")
    for pattern, n in sorted(comparison["mismatch_pattern"].items()):
        print(f"    {pattern}: {n}")

    print()
    print("# I. LEAKAGE CHECK")
    print(f"  Forbidden features pada inference dataset : "
          f"dicek otomatis (schema validation + feature store)")
    print(f"  Kolom prediksi                           : id + feature + label + "
          f"probabilitas + timestamp + version + variant")

    print()
    print("# J. OUTPUT FILE (PARQUET BIASA, BUKAN ICEBERG)")
    for variant, vr in report["variants"].items():
        print(f"  [{variant}] {vr['output_parquet']}")
    print("  [comparison] data/predictions/prediction_comparison.parquet")

    print()
    print("# K. QUALITY REPORT")
    print("  logs/inference_quality_report.json")

    print()
    print("# L. STATUS")
    print(f"  {report['status']}")
    print("=" * 88)