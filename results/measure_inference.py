"""
Mengukur waktu inference Gaussian Naive Bayes (tanpa vs dengan SMOTE)
untuk Bab 4 skripsi.

Metodologi:
  - TIDAK menyentuh pipeline ETL / feature store / model / hasil prediksi.
  - Inference dataset dibaca EAGER lewat pyarrow dari parquet aktif
    (current snapshot) tabel Iceberg `feature_store.inference_dataset`
    -- TANPA Spark.
  - Model v2.0.0 di-load dari registry (joblib). Bukan menimpa apa pun.
  - Yang diukur adalah eksekusi SKLEARN (eager numpy), BUKAN pembentukan
    execution plan Spark. Tidak ada lazy evaluation pada wilayah pengukuran.
  - Komponen yang diukur:
      A. input preparation (build_X dari pandas -> numpy)
      B. model loading (load_model -> joblib.load)
      C. actual prediction (predict)
      D. predict_proba
      E. end-to-end inference (input prep + model load + predict + proba)
  - Warm-up 1x di luar statistik, lalu 5x run pengukuran.
  - Statistik: mean / min / max / std / median.
  - VALIDASI: prediksi yang dihasilkan script harus menghasilkan distribusi
    yang SAMA dengan hasil prediksi produksi (data/predictions/*.parquet).
    Ini bukti bahwa expression prediction benar-benar dievaluasi.
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

from iceberg_reader import load_active_parquet

from backend.ml.registry import load_model, MODEL_VERSION, MODEL_NAME
from backend.ml.inference import (
    INFERENCE_FEATURES,
    IDENTIFIER_COLUMN,
    PREDICTION_LABEL_COLUMN,
)

RESULT_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "iceberg" / "feature_store" / "inference_dataset"
PROD_DIR = PROJECT_ROOT / "data" / "predictions"
N_RUNS = 5
WARMUP_N = 1

TIMER = time.perf_counter


def _elapsed(start):
    return TIMER() - start


def _summarize(times):
    return {
        "mean_sec": round(statistics.mean(times), 9),
        "median_sec": round(statistics.median(times), 9),
        "min_sec": round(min(times), 9),
        "max_sec": round(max(times), 9),
        "std_sec": round(statistics.stdev(times), 9) if len(times) > 1 else 0.0,
    }


def _stats(scenario, stage, rows, times, extra=None):
    row = {
        "category": "inference",
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


def build_X(pdf):
    return pdf[INFERENCE_FEATURES].astype(float).to_numpy()


def main() -> None:
    print("=" * 70)
    print("PENGUKURAN WAKTU INFERENCE GAUSSIAN NB (tanpa/dengan SMOTE)")
    print("Dataset: feature_store.inference_dataset (parquet aktif, eager)")
    print("Runtime: sklearn pada numpy (EAGER, bukan Spark)")
    print("=" * 70)

    # -----------------------------------------------------
    # Load inference dataset SEKALI (di luar pengukuran)
    # -----------------------------------------------------
    pdf = load_active_parquet(str(DATA_DIR))
    X = build_X(pdf)
    n_rows, n_features = X.shape
    distinct_id = int(pdf[IDENTIFIER_COLUMN].nunique())
    assert n_rows == 14926, f"VALIDASI GAGAL: inference rows {n_rows} != 14926"
    assert distinct_id == n_rows, "VALIDASI GAGAL: id tidak unik"
    print(f"Rows         : {n_rows}")
    print(f"Distinct id  : {distinct_id}")
    print(f"Features     : {n_features}")
    print(f"Runs         : {N_RUNS} (warm-up {WARMUP_N}x di luar statistik)")

    # -----------------------------------------------------
    # Hasil produksi (untuk validasi kesesuaian prediksi)
    # -----------------------------------------------------
    prod = {
        "without_smote": pd.read_parquet(
            PROD_DIR / "prediction_result_without_smote.parquet"),
        "with_smote": pd.read_parquet(
            PROD_DIR / "prediction_result_with_smote.parquet"),
    }

    per_run = []

    variants = [
        {"key": "without_smote", "use_smote": False, "display": "without_smote"},
        {"key": "with_smote", "use_smote": True, "display": "with_smote"},
    ]

    summary_rows = []

    for var in variants:
        key = var["key"]
        disp = var["display"]
        use_smote = var["use_smote"]

        print("-" * 70)
        print(f"SKENARIO: {disp.upper()}")

        # Warm-up (tidak dihitung)
        pipe, meta = load_model(use_smote=use_smote)
        pipe.predict(X[:200])
        pipe.predict_proba(X[:200])
        print("  Warm-up selesai.")

        # A. input preparation (build_X)
        times_inp = []
        for run in range(1, N_RUNS + 1):
            t0 = TIMER()
            _ = build_X(pdf)
            times_inp.append(_elapsed(t0))
            per_run.append({
                "run": run, "category": "inference", "scenario": f"inference_{key}",
                "stage": "input_preparation", "variant": key, "rows": n_rows,
                "time_sec": round(times_inp[-1], 9),
            })
        print(f"  A. input_preparation  mean={statistics.mean(times_inp)*1000:.4f} ms")

        # B. model loading
        times_load = []
        for run in range(1, N_RUNS + 1):
            t0 = TIMER()
            _, _meta = load_model(use_smote=use_smote)
            times_load.append(_elapsed(t0))
            per_run.append({
                "run": run, "category": "inference", "scenario": f"inference_{key}",
                "stage": "model_load", "variant": key, "rows": n_rows,
                "time_sec": round(times_load[-1], 9),
            })
        print(f"  B. model_load          mean={statistics.mean(times_load)*1000:.4f} ms")

        # model terakhir (untuk predict)
        pipe, meta = load_model(use_smote=use_smote)

        # C. actual prediction
        times_pred = []
        for run in range(1, N_RUNS + 1):
            t0 = TIMER()
            y_pred = pipe.predict(X)
            times_pred.append(_elapsed(t0))
            per_run.append({
                "run": run, "category": "inference", "scenario": f"inference_{key}",
                "stage": "predict", "variant": key, "rows": n_rows,
                "time_sec": round(times_pred[-1], 9),
            })
        print(f"  C. predict             mean={statistics.mean(times_pred)*1000:.4f} ms")

        # D. predict_proba
        times_proba = []
        for run in range(1, N_RUNS + 1):
            t0 = TIMER()
            _ = pipe.predict_proba(X)
            times_proba.append(_elapsed(t0))
            per_run.append({
                "run": run, "category": "inference", "scenario": f"inference_{key}",
                "stage": "predict_proba", "variant": key, "rows": n_rows,
                "time_sec": round(times_proba[-1], 9),
            })
        print(f"  D. predict_proba       mean={statistics.mean(times_proba)*1000:.4f} ms")

        # E. end-to-end (input prep + model load + predict + proba)
        times_e2e = []
        for run in range(1, N_RUNS + 1):
            t0 = TIMER()
            _X = build_X(pdf)
            _pipe, _m = load_model(use_smote=use_smote)
            _y = _pipe.predict(_X)
            _proba = _pipe.predict_proba(_X)
            times_e2e.append(_elapsed(t0))
            per_run.append({
                "run": run, "category": "inference", "scenario": f"inference_{key}",
                "stage": "end_to_end", "variant": key, "rows": n_rows,
                "time_sec": round(times_e2e[-1], 9),
            })
        print(f"  E. end_to_end          mean={statistics.mean(times_e2e)*1000:.4f} ms")

        # -----------------------------------------------------
        # VALIDASI: prediksi harus cocok dgn hasil produksi
        # -----------------------------------------------------
        final_pred = pipe.predict(X)
        final_proba = pipe.predict_proba(X)
        # pastikan expression benar-benar dievaluasi (bukan lazy):
        assert len(final_pred) == n_rows
        assert final_proba.shape == (n_rows, len(meta["class_mapping"]))

        class_mapping = meta["class_mapping"]
        index_to_label = {int(v): k for k, v in class_mapping.items()}
        labels = pd.Series([index_to_label[int(i)] for i in final_pred],
                           name=PREDICTION_LABEL_COLUMN)

        # cocokkan id -> prediksi dgn hasil produksi
        mine = pd.DataFrame({IDENTIFIER_COLUMN: pdf[IDENTIFIER_COLUMN],
                             PREDICTION_LABEL_COLUMN: labels.values})
        prod_pdf = prod[key]
        merged = mine.merge(
            prod_pdf[[IDENTIFIER_COLUMN, PREDICTION_LABEL_COLUMN]],
            on=IDENTIFIER_COLUMN, suffixes=("_mine", "_prod"))
        agreement = int((merged["prediksi_status_kelulusan_mine"] ==
                         merged["prediksi_status_kelulusan_prod"]).sum())
        total = len(merged)
        rate = agreement / total * 100
        print(f"  VALIDASI {key}: agreement dgn hasil produksi = "
              f"{agreement}/{total} ({rate:.2f}%)")
        assert rate == 100.0, (
            f"VALIDASI GAGAL {key}: prediksi script tidak 100% cocok dgn produksi "
            f"({rate:.2f}%)"
        )

        summary_rows.append(_stats(f"inference_{key}", "input_preparation",
                                   n_rows, times_inp))
        summary_rows.append(_stats(f"inference_{key}", "model_load",
                                   n_rows, times_load))
        summary_rows.append(_stats(f"inference_{key}", "predict", n_rows, times_pred))
        summary_rows.append(_stats(f"inference_{key}", "predict_proba",
                                   n_rows, times_proba))
        summary_rows.append(_stats(f"inference_{key}", "end_to_end",
                                   n_rows, times_e2e))

    # -----------------------------------------------------
    # Simpan per-run CSV
    # -----------------------------------------------------
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(per_run).to_csv(RESULT_DIR / "inference_timing.csv", index=False)
    print(f"\nPer-run tersimpan : {RESULT_DIR / 'inference_timing.csv'}")

    # -----------------------------------------------------
    # Ringkasan statistik + simpan timing_summary.csv
    # -----------------------------------------------------
    summary_csv = RESULT_DIR / "timing_summary.csv"
    if summary_csv.exists():
        existing = pd.read_csv(summary_csv)
        existing = existing[existing["category"] != "inference"]
        combined = pd.concat([existing, pd.DataFrame(summary_rows)], ignore_index=True)
    else:
        combined = pd.DataFrame(summary_rows)
    combined.to_csv(summary_csv, index=False)
    print(f"Ringkasan tersimpan : {summary_csv}")

    print("=" * 70)
    print("RINGKASAN WAKTU INFERENCE (detik)")
    print("=" * 70)
    for r in summary_rows:
        print(f"  {r['scenario']:<28} {r['stage']:<20} "
              f"mean={r['mean_sec']:.6f} med={r['median_sec']:.6f} "
              f"min={r['min_sec']:.6f} max={r['max_sec']:.6f} std={r['std_sec']:.6f}")

    # Throughput (rows/detik) dari mean predict -- hati-hati: ini throughput
    # in-memory numpy, bukan end-to-end produksi.
    print("=" * 70)
    print("THROUGHPUT (rows/detik) berbasis mean predict (in-memory numpy):")
    for var in variants:
        key = var["key"]
        # ambil mean predict dari summary_rows
        row = [r for r in summary_rows if r["scenario"] == f"inference_{key}"
               and r["stage"] == "predict"][0]
        thr = n_rows / row["mean_sec"]
        print(f"  {key}: {thr:,.0f} rows/s  (per-row: {row['mean_sec']/n_rows*1e9:.1f} ns)")

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------
    meta_out = {
        "script": "measure_inference.py",
        "source": "local.feature_store.inference_dataset (parquet aktif, eager, tanpa Spark)",
        "rows": n_rows,
        "distinct_id": distinct_id,
        "n_features": n_features,
        "n_runs": N_RUNS,
        "warmup_runs": WARMUP_N,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "eager": True,
        "spark_lazy_eval": False,
        "components_measured": [
            "input_preparation", "model_load", "predict", "predict_proba",
            "end_to_end",
        ],
        "validation": {
            "rows_14926": True,
            "unique_id": True,
            "agreement_with_production_percent": 100.0,
        },
        "summary_sec": {r["scenario"] + "_" + r["stage"]: _summarize(
            [0]) if False else {
                "mean_sec": r["mean_sec"], "median_sec": r["median_sec"],
                "min_sec": r["min_sec"], "max_sec": r["max_sec"],
                "std_sec": r["std_sec"],
            } for r in summary_rows},
    }
    with open(RESULT_DIR / "inference_timing_meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta_out, fh, ensure_ascii=False, indent=2)
    print(f"Metadata tersimpan : {RESULT_DIR / 'inference_timing_meta.json'}")


if __name__ == "__main__":
    main()