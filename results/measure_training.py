"""
Mengukur waktu training Gaussian Naive Bayes (tanpa vs dengan SMOTE)
untuk Bab 4 skripsi.

Metodologi:
  - TIDAK menyentuh pipeline ETL / feature store / dataset / model.
  - Dataset dibaca EAGER lewat pyarrow dari parquet aktif (current snapshot)
    tabel Iceberg `feature_store.training_dataset` -- TANPA Spark.
  - Yang diukur adalah eksekusi SKLEARN/IMBALED-LEARN (eager numpy),
    BUKAN pembentukan execution plan Spark. Tidak ada lazy evaluation
    pada wilayah pengukuran.
  - Warm-up 1x di luar statistik, lalu 5x run pengukuran.
  - Statistik: mean / min / max / std / median.
  - Validasi: hasil fit harus sesuai (class_count_, jumlah baris setelah
    SMOTE) sebagai bukti bahwa komputasi benar-benar dieksekusi.
"""

import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.naive_bayes import GaussianNB

from iceberg_reader import load_active_parquet

from backend.ml.data_preparation import (
    build_target_encoding,
    encode_target,
    numpy_X,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    POSITIVE_CLASS,
)
from backend.ml.train import build_estimator, RANDOM_STATE

RESULT_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "iceberg" / "feature_store" / "training_dataset"
N_RUNS = 5
WARMUP_N = 1

TIMER = time.perf_counter


def _elapsed(start):
    return TIMER() - start


def _stats(scenario, stage, rows, times, extra=None):
    row = {
        "category": "training",
        "scenario": scenario,
        "stage": stage,
        "rows": rows,
        "runs": len(times),
        "mean_sec": round(statistics.mean(times), 9),
        "median_sec": round(statistics.median(times), 9),
        "min_sec": round(min(times), 9),
        "max_sec": round(max(times), 9),
        "std_sec": round(statistics.stdev(times), 9) if len(times) > 1 else 0.0,
    }
    if extra:
        row.update(extra)
    return row


def _summarize(times):
    return {
        "mean_sec": round(statistics.mean(times), 9),
        "median_sec": round(statistics.median(times), 9),
        "min_sec": round(min(times), 9),
        "max_sec": round(max(times), 9),
        "std_sec": round(statistics.stdev(times), 9) if len(times) > 1 else 0.0,
    }


def main() -> None:
    print("=" * 70)
    print("PENGUKURAN WAKTU TRAINING GAUSSIAN NB (tanpa/dengan SMOTE)")
    print("Dataset: feature_store.training_dataset (parquet aktif, eager)")
    print("Runtime: sklearn/imblearn pada numpy (EAGER, bukan Spark)")
    print("=" * 70)

    # -----------------------------------------------------
    # Load dataset SEKALI (di luar pengukuran)
    # -----------------------------------------------------
    pdf = load_active_parquet(str(DATA_DIR))
    class_mapping = build_target_encoding(pdf)
    y = encode_target(pdf, class_mapping).to_numpy()
    X = numpy_X(pdf)

    n_rows, n_features = X.shape
    class_distribution = {k: int(v) for k, v in pdf[TARGET_COLUMN].value_counts().items()}
    print(f"Rows         : {n_rows}")
    print(f"Features     : {n_features}")
    print(f"Class map    : {class_mapping}")
    print(f"Distribusi   : {class_distribution}")
    print(f"Runs         : {N_RUNS} (warm-up {WARMUP_N}x di luar statistik)")

    # -----------------------------------------------------
    # Warm-up (tidak dihitung)
    # -----------------------------------------------------
    _warmup_fit = build_estimator(use_smote=False)
    _warmup_fit.fit(X, y)
    _warmup_fit = build_estimator(use_smote=True)
    _warmup_fit.fit(X, y)
    print("Warm-up selesai (di luar pengukuran).")

    per_run = []

    # -----------------------------------------------------
    # A. TRAINING TANPA SMOTE  (GaussianNB.fit pada 13.347)
    # -----------------------------------------------------
    times_a = []
    for run in range(1, N_RUNS + 1):
        est = build_estimator(use_smote=False)
        t0 = TIMER()
        est.fit(X, y)
        times_a.append(_elapsed(t0))
        per_run.append({
            "run": run, "category": "training",
            "scenario": "training_without_smote", "stage": "fit",
            "variant": "without_smote", "rows": n_rows,
            "time_sec": round(times_a[-1], 9),
        })
        print(f"[without_smote] run {run}: fit={times_a[-1]*1000:.4f} ms")

    # Validasi A: benar-benar terfit (class_count_ sesuai distribusi)
    _check = build_estimator(use_smote=False)
    _check.fit(X, y)
    class_count_ = np.bincount(y, minlength=len(class_mapping))
    learned = np.array(_check.class_count_, dtype=int)
    assert (learned == class_count_).all(), (
        f"VALIDASI GAGAL: class_count_ model ({learned}) != distribusi data ({class_count_})"
    )
    print(f"VALIDASI A PASS: GaussianNB benar-benar ter-fit "
          f"(class_count_={learned.tolist()}).")

    # -----------------------------------------------------
    # B. TRAINING DENGAN SMOTE -- preprocessing (SMOTE saja)
    # -----------------------------------------------------
    # Satu resample di luar pengukuran untuk mendapatkan X_res/y_res
    # yang dipakai mengukur fit GaussianNB setelah SMOTE.
    smote_fixed = SMOTE(random_state=RANDOM_STATE)
    X_res, y_res = smote_fixed.fit_resample(X, y)
    n_rows_res = X_res.shape[0]
    dist_res = np.bincount(y_res, minlength=len(class_mapping))
    assert n_rows_res == 20272, (
        f"VALIDASI GAGAL: jumlah baris setelah SMOTE {n_rows_res} != 20272"
    )
    assert dist_res[0] == dist_res[1], (
        f"VALIDASI GAGAL: kelas tidak seimbang setelah SMOTE {dist_res}"
    )
    print(f"SMOTE reference : {n_rows} -> {n_rows_res} rows "
          f"(distribusi={dist_res.tolist()}). VALIDASI B1 PASS.")

    times_b_smote = []
    for run in range(1, N_RUNS + 1):
        smote = SMOTE(random_state=RANDOM_STATE)
        t0 = TIMER()
        X_r, y_r = smote.fit_resample(X, y)
        times_b_smote.append(_elapsed(t0))
        assert X_r.shape[0] == n_rows_res
        per_run.append({
            "run": run, "category": "training",
            "scenario": "training_with_smote", "stage": "smote_fit_resample",
            "variant": "with_smote", "rows": n_rows,
            "resampled_rows": n_rows_res,
            "time_sec": round(times_b_smote[-1], 9),
        })
        print(f"[with_smote]    run {run}: SMOTE fit_resample={times_b_smote[-1]*1000:.4f} ms")

    # -----------------------------------------------------
    # C. TRAINING DENGAN SMOTE -- fit GaussianNB setelah SMOTE
    # -----------------------------------------------------
    times_b_gnb = []
    for run in range(1, N_RUNS + 1):
        gnb = GaussianNB()
        t0 = TIMER()
        gnb.fit(X_res, y_res)
        times_b_gnb.append(_elapsed(t0))
        per_run.append({
            "run": run, "category": "training",
            "scenario": "training_with_smote", "stage": "gnb_fit_after_smote",
            "variant": "with_smote", "rows": n_rows_res,
            "resampled_rows": n_rows_res,
            "time_sec": round(times_b_gnb[-1], 9),
        })
        print(f"[with_smote]    run {run}: GaussianNB fit (after SMOTE)="
              f"{times_b_gnb[-1]*1000:.4f} ms")

    # -----------------------------------------------------
    # D. TRAINING DENGAN SMOTE -- TOTAL (ImbPipeline: SMOTE + GNB)
    # -----------------------------------------------------
    times_b_total = []
    for run in range(1, N_RUNS + 1):
        pipe = build_estimator(use_smote=True)
        t0 = TIMER()
        pipe.fit(X, y)
        times_b_total.append(_elapsed(t0))
        per_run.append({
            "run": run, "category": "training",
            "scenario": "training_with_smote", "stage": "fit_total",
            "variant": "with_smote", "rows": n_rows,
            "resampled_rows": n_rows_res,
            "time_sec": round(times_b_total[-1], 9),
        })
        print(f"[with_smote]    run {run}: TOTAL (SMOTE+GNB)={times_b_total[-1]*1000:.4f} ms")

    # Validasi D: model di pipeline benar-benar terfit
    assert hasattr(pipe.named_steps["model"], "theta_")
    print("VALIDASI B2 PASS: ImbPipeline benar-benar ter-fit (theta_ tersedia).")

    # -----------------------------------------------------
    # Simpan per-run CSV
    # -----------------------------------------------------
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(per_run).to_csv(RESULT_DIR / "training_timing.csv", index=False)
    print(f"\nPer-run tersimpan : {RESULT_DIR / 'training_timing.csv'}")

    # -----------------------------------------------------
    # Ringkasan statistik + simpan timing_summary.csv
    # -----------------------------------------------------
    summary_rows = [
        _stats("training_without_smote", "fit", n_rows, times_a),
        _stats("training_with_smote", "smote_fit_resample", n_rows, times_b_smote,
               {"resampled_rows": n_rows_res}),
        _stats("training_with_smote", "gnb_fit_after_smote", n_rows_res, times_b_gnb,
               {"resampled_rows": n_rows_res}),
        _stats("training_with_smote", "fit_total", n_rows, times_b_total,
               {"resampled_rows": n_rows_res}),
    ]

    summary_csv = RESULT_DIR / "timing_summary.csv"
    if summary_csv.exists():
        existing = pd.read_csv(summary_csv)
        existing = existing[existing["category"] != "training"]
        combined = pd.concat([existing, pd.DataFrame(summary_rows)], ignore_index=True)
    else:
        combined = pd.DataFrame(summary_rows)
    combined.to_csv(summary_csv, index=False)
    print(f"Ringkasan tersimpan : {summary_csv}")

    print("=" * 70)
    print("RINGKASAN WAKTU TRAINING (detik)")
    print("=" * 70)
    for r in summary_rows:
        print(f"  {r['scenario']:<28} {r['stage']:<20} "
              f"mean={r['mean_sec']:.6f} med={r['median_sec']:.6f} "
              f"min={r['min_sec']:.6f} max={r['max_sec']:.6f} std={r['std_sec']:.6f}")

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------
    meta = {
        "script": "measure_training.py",
        "source": "local.feature_store.training_dataset (parquet aktif, eager, tanpa Spark)",
        "rows_before_smote": n_rows,
        "rows_after_smote": int(n_rows_res),
        "n_features": n_features,
        "class_mapping": class_mapping,
        "class_distribution": class_distribution,
        "random_state": RANDOM_STATE,
        "n_runs": N_RUNS,
        "warmup_runs": WARMUP_N,
        "model": "GaussianNB",
        "with_smote_pipeline": "ImbPipeline(SMOTE + GaussianNB)",
        "eager": True,
        "spark_lazy_eval": False,
        "validation": {
            "without_smote_class_count_matches": True,
            "after_smote_rows": int(n_rows_res),
            "after_smote_balanced": True,
        },
        "summary_sec": {
            "without_smote_fit": _summarize(times_a),
            "with_smote_smote": _summarize(times_b_smote),
            "with_smote_gnb_fit": _summarize(times_b_gnb),
            "with_smote_total": _summarize(times_b_total),
        },
    }
    with open(RESULT_DIR / "training_timing_meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"Metadata tersimpan : {RESULT_DIR / 'training_timing_meta.json'}")


if __name__ == "__main__":
    main()
