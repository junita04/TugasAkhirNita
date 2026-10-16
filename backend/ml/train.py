import numpy as np
import pandas as pd
import joblib
import json
import time
import warnings
from pathlib import Path
from sklearn.naive_bayes import CategoricalNB, GaussianNB
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

from hybrid_nb import HybridNaiveBayes

from backend.config.namespaces import model_dir

warnings.filterwarnings("ignore")

WEIGHT_GRID = np.arange(0.1, 1.0, 0.1)
CV_FOLDS = 10
RANDOM_STATE = 42


def hitung_metrik_manual(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    return precision, recall, f1


def train_model(X_train, y_train, X_test, y_test, cat_cols, num_cols, model_name):
    print(f"\n{'='*70}")
    print(f"Training {model_name}")
    print(f"{'='*70}")
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")
    print(f"Categorical: {cat_cols}")
    print(f"Numerical: {num_cols}")

    X_train_cat = X_train[cat_cols].astype(int).values
    X_train_num = X_train[num_cols].astype(float).values
    X_test_cat = X_test[cat_cols].astype(int).values
    X_test_num = X_test[num_cols].astype(float).values

    num_classes = len(np.unique(y_train))
    print(f"Jumlah kelas: {num_classes}")
    print(f"Jumlah kombinasi bobot: {len(WEIGHT_GRID)}")

    start_total = time.perf_counter()

    hasil_optimasi = []
    hasil_cm = []
    hasil_per_fold = []

    skf = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    for weight_cat in WEIGHT_GRID:
        weight_cat = round(float(weight_cat), 1)
        weight_gauss = round(1.0 - weight_cat, 1)

        print(f"\nMenguji bobot: Cat={weight_cat:.1f}, Gauss={weight_gauss:.1f}")

        oof_probabilities = np.zeros((len(X_train), num_classes))

        for fold, (train_idx, valid_idx) in enumerate(skf.split(X_train, y_train), start=1):
            X_fold_train_cat = X_train_cat[train_idx]
            X_fold_train_num = X_train_num[train_idx]
            y_fold_train = y_train.iloc[train_idx]

            X_fold_valid_cat = X_train_cat[valid_idx]
            X_fold_valid_num = X_train_num[valid_idx]
            y_fold_valid = y_train.iloc[valid_idx]

            fold_model = HybridNaiveBayes(weight_cat=weight_cat, weight_gauss=weight_gauss)
            fold_model.fit(X_fold_train_cat, X_fold_train_num, y_fold_train)

            fold_probabilities = fold_model.predict_proba(X_fold_valid_cat, X_fold_valid_num)
            oof_probabilities[valid_idx] = fold_probabilities

            pred_fold = np.argmax(fold_probabilities, axis=1)

            hasil_per_fold.append({
                "Weight Cat": weight_cat,
                "Weight Gauss": weight_gauss,
                "Fold": fold,
                "Jumlah Data Validasi": len(valid_idx),
                "Accuracy": accuracy_score(y_fold_valid, pred_fold),
                "Precision Tepat Waktu": precision_score(y_fold_valid, pred_fold, pos_label=0, zero_division=0),
                "Recall Tepat Waktu": recall_score(y_fold_valid, pred_fold, pos_label=0, zero_division=0),
                "F1 Tepat Waktu": f1_score(y_fold_valid, pred_fold, pos_label=0, zero_division=0),
                "Precision Terlambat": precision_score(y_fold_valid, pred_fold, pos_label=1, zero_division=0),
                "Recall Terlambat": recall_score(y_fold_valid, pred_fold, pos_label=1, zero_division=0),
                "F1 Terlambat": f1_score(y_fold_valid, pred_fold, pos_label=1, zero_division=0),
            })

        predictions = np.argmax(oof_probabilities, axis=1)

        cm = confusion_matrix(y_train, predictions, labels=[0, 1])
        tp0, fn0, fp0, tn0 = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
        tp1, fn1, fp1, tn1 = cm[1, 1], cm[1, 0], cm[0, 1], cm[0, 0]

        precision_tepat, recall_tepat, f1_tepat = hitung_metrik_manual(tp0, fp0, fn0)
        precision_terlambat, recall_terlambat, f1_terlambat = hitung_metrik_manual(tp1, fp1, fn1)
        accuracy = (tp0 + tp1) / cm.sum()

        assert np.isclose(precision_tepat, precision_score(y_train, predictions, pos_label=0, zero_division=0))
        assert np.isclose(recall_tepat, recall_score(y_train, predictions, pos_label=0, zero_division=0))
        assert np.isclose(f1_tepat, f1_score(y_train, predictions, pos_label=0, zero_division=0))
        assert np.isclose(precision_terlambat, precision_score(y_train, predictions, pos_label=1, zero_division=0))
        assert np.isclose(recall_terlambat, recall_score(y_train, predictions, pos_label=1, zero_division=0))
        assert np.isclose(f1_terlambat, f1_score(y_train, predictions, pos_label=1, zero_division=0))
        assert np.isclose(accuracy, accuracy_score(y_train, predictions))

        hasil_cm.append({
            "Weight Cat": weight_cat,
            "Weight Gauss": weight_gauss,
            "TP Tepat (TP0)": int(tp0),
            "FN Tepat (FN0)": int(fn0),
            "FP Tepat (FP0)": int(fp0),
            "TP Terlambat (TP1)": int(tp1),
            "Total Data": int(cm.sum())
        })

        hasil_optimasi.append({
            "Weight Cat": weight_cat,
            "Weight Gauss": weight_gauss,
            "Total Weight": weight_cat + weight_gauss,
            "Accuracy": accuracy,
            "Precision Tepat Waktu": precision_tepat,
            "Recall Tepat Waktu": recall_tepat,
            "F1 Tepat Waktu": f1_tepat,
            "Precision Terlambat": precision_terlambat,
            "Recall Terlambat": recall_terlambat,
            "F1 Terlambat": f1_terlambat,
        })

    hasil_optimasi_df = pd.DataFrame(hasil_optimasi)
    hasil_cm_df = pd.DataFrame(hasil_cm)
    hasil_per_fold_df = pd.DataFrame(hasil_per_fold)

    end_total = time.perf_counter()
    print(f"\nOPTIMASI SELESAI ({end_total - start_total:.2f} detik)")
    print(f"Kombinasi diuji: {len(hasil_optimasi_df)}")

    print("\n" + "="*100)
    print("HASIL OPTIMASI BOBOT HYBRID NAIVE BAYES (STRATIFIED 10-FOLD CV)")
    print("="*100)
    print(hasil_optimasi_df.sort_values(
        by=["F1 Tepat Waktu", "Recall Tepat Waktu", "Precision Tepat Waktu"],
        ascending=False
    ).round(4).to_string(index=False))

    print("\n" + "="*100)
    print("CONFUSION MATRIX PER BOBOT (OOF)")
    print("="*100)
    print(hasil_cm_df.sort_values("Weight Cat", ascending=False).to_string(index=False))

    print("\n" + "="*100)
    print("AKURASI PER FOLD")
    print("="*100)
    tabel_acc_fold = hasil_per_fold_df.pivot_table(
        index=["Weight Cat", "Weight Gauss"], columns="Fold", values="Accuracy"
    )
    kolom_fold = list(tabel_acc_fold.columns)
    tabel_acc_fold["Mean"] = tabel_acc_fold[kolom_fold].mean(axis=1)
    tabel_acc_fold["Std"] = tabel_acc_fold[kolom_fold].std(axis=1)
    print(tabel_acc_fold.sort_index(ascending=False).round(4).to_string())

    hasil_terbaik = hasil_optimasi_df.sort_values(
        by=["F1 Tepat Waktu", "Recall Tepat Waktu", "Precision Tepat Waktu"],
        ascending=False
    ).iloc[0]

    weight_cat_terbaik = hasil_terbaik["Weight Cat"]
    weight_gauss_terbaik = hasil_terbaik["Weight Gauss"]

    print("\n" + "="*70)
    print("HASIL BOBOT TERBAIK")
    print("="*70)
    print(f"Weight Cat   : {weight_cat_terbaik:.1f}")
    print(f"Weight Gauss : {weight_gauss_terbaik:.1f}")
    print(f"Total Weight : {weight_cat_terbaik + weight_gauss_terbaik:.1f}")
    print(f"Accuracy              : {hasil_terbaik['Accuracy']:.4f}")
    print(f"Precision Tepat Waktu : {hasil_terbaik['Precision Tepat Waktu']:.4f}")
    print(f"Recall Tepat Waktu    : {hasil_terbaik['Recall Tepat Waktu']:.4f}")
    print(f"F1 Tepat Waktu        : {hasil_terbaik['F1 Tepat Waktu']:.4f}")
    print(f"Precision Terlambat   : {hasil_terbaik['Precision Terlambat']:.4f}")
    print(f"Recall Terlambat      : {hasil_terbaik['Recall Terlambat']:.4f}")
    print(f"F1 Terlambat          : {hasil_terbaik['F1 Terlambat']:.4f}")

    print("\n" + "="*70)
    print(f"DETAIL PER FOLD - BOBOT TERBAIK (Cat={weight_cat_terbaik:.1f}, Gauss={weight_gauss_terbaik:.1f})")
    print("="*70)
    detail_terbaik = hasil_per_fold_df[
        (hasil_per_fold_df["Weight Cat"] == round(weight_cat_terbaik, 1)) &
        (hasil_per_fold_df["Weight Gauss"] == round(weight_gauss_terbaik, 1))
    ].reset_index(drop=True)
    print(detail_terbaik.round(4).to_string(index=False))

    print("\nRingkasan antar fold (mean ± std):")
    kolom_metrik = [
        "Accuracy", "Precision Tepat Waktu", "Recall Tepat Waktu", "F1 Tepat Waktu",
        "Precision Terlambat", "Recall Terlambat", "F1 Terlambat"
    ]
    for kolom in kolom_metrik:
        print(f"{kolom:<24}: {detail_terbaik[kolom].mean():.4f} ± {detail_terbaik[kolom].std():.4f}")

    print("\n" + "="*70)
    print("TRAINING MODEL FINAL")
    print("="*70)

    model_final = HybridNaiveBayes(weight_cat=weight_cat_terbaik, weight_gauss=weight_gauss_terbaik)
    model_final.fit(X_train_cat, X_train_num, y_train)

    test_predictions = model_final.predict(X_test_cat, X_test_num)
    test_probabilities = model_final.predict_proba(X_test_cat, X_test_num)

    cm_test = confusion_matrix(y_test, test_predictions, labels=[0, 1])
    tp0, fn0, fp0, tn0 = cm_test[0, 0], cm_test[0, 1], cm_test[1, 0], cm_test[1, 1]
    tp1, fn1, fp1, tn1 = cm_test[1, 1], cm_test[1, 0], cm_test[0, 1], cm_test[0, 0]

    precision_tepat, recall_tepat, f1_tepat = hitung_metrik_manual(tp0, fp0, fn0)
    precision_terlambat, recall_terlambat, f1_terlambat = hitung_metrik_manual(tp1, fp1, fn1)
    accuracy_test = (tp0 + tp1) / cm_test.sum()

    print("\n" + "="*70)
    print("EVALUASI HOLDOUT TESTING")
    print("="*70)
    print(f"Confusion Matrix:")
    print(f"  Aktual Tepat -> Pred Tepat (TP Tepat)      : {tp0}")
    print(f"  Aktual Tepat -> Pred Terlambat (FN Tepat)  : {fn0}")
    print(f"  Aktual Terlambat -> Pred Tepat (FP Tepat)  : {fp0}")
    print(f"  Aktual Terlambat -> Pred Terlambat (TP Terl): {tp1}")
    print(f"\n  Accuracy              : {accuracy_test:.4f}")
    print(f"  Precision Tepat Waktu : {precision_tepat:.4f}")
    print(f"  Recall Tepat Waktu    : {recall_tepat:.4f}")
    print(f"  F1 Tepat Waktu        : {f1_tepat:.4f}")
    print(f"  Precision Terlambat   : {precision_terlambat:.4f}")
    print(f"  Recall Terlambat      : {recall_terlambat:.4f}")
    print(f"  F1 Terlambat          : {f1_terlambat:.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, test_predictions, target_names=["Tepat Waktu", "Terlambat"], zero_division=0))

    out_dir = model_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / f"{model_name}.joblib"
    meta_path = out_dir / f"{model_name}_metadata.json"

    joblib.dump(model_final, model_path)

    metadata = {
        "model_name": model_name,
        "weight_cat": float(weight_cat_terbaik),
        "weight_gauss": float(weight_gauss_terbaik),
        "categorical_features": cat_cols,
        "numerical_features": num_cols,
        "cv_folds": CV_FOLDS,
        "cv_results": {
            "best_params": {"weight_cat": float(weight_cat_terbaik), "weight_gauss": float(weight_gauss_terbaik)},
            "best_oof_metrics": {k: float(v) for k, v in hasil_terbaik.items()},
            "per_fold_summary": {k: {"mean": float(detail_terbaik[k].mean()), "std": float(detail_terbaik[k].std())}
                                 for k in kolom_metrik}
        },
        "holdout_metrics": {
            "accuracy": float(accuracy_test),
            "precision_tepat_waktu": float(precision_tepat),
            "recall_tepat_waktu": float(recall_tepat),
            "f1_tepat_waktu": float(f1_tepat),
            "precision_terlambat": float(precision_terlambat),
            "recall_terlambat": float(recall_terlambat),
            "f1_terlambat": float(f1_terlambat),
            "confusion_matrix": {
                "tp_tepat": int(tp0), "fn_tepat": int(fn0),
                "fp_tepat": int(fp0), "tp_terlambat": int(tp1)
            }
        }
    }

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel disimpan: {model_path}")
    print(f"Metadata disimpan: {meta_path}")

    return model_final, metadata


def load_model(model_name):
    out_dir = model_dir()
    model_path = out_dir / f"{model_name}.joblib"
    meta_path = out_dir / f"{model_name}_metadata.json"
    model = joblib.load(model_path)
    with open(meta_path) as f:
        metadata = json.load(f)
    return model, metadata


if __name__ == "__main__":
    from data_preparation import get_model_a_data, get_model_b_data, get_feature_config

    print("\n" + "="*80)
    print("TRAINING MODEL A (UTAMA): total_sks, jumlah_mk")
    print("="*80)
    X_train_a, X_test_a, y_train_a, y_test_a = get_model_a_data()
    features_a = get_feature_config("A")

    model_a, metadata_a = train_model(
        X_train_a, y_train_a, X_test_a, y_test_a,
        features_a["categorical"], features_a["numerical"],
        "model_a_utama"
    )

    print("\n" + "="*80)
    print("TRAINING MODEL B (PEMBANDING): selisih_sks, kecepatan_sks_per_semester")
    print("="*80)
    X_train_b, X_test_b, y_train_b, y_test_b = get_model_b_data()
    features_b = get_feature_config("B")

    model_b, metadata_b = train_model(
        X_train_b, y_train_b, X_test_b, y_test_b,
        features_b["categorical"], features_b["numerical"],
        "model_b_pembanding"
    )

    print("\n" + "="*80)
    print("PERBANDINGAN MODEL A vs MODEL B")
    print("="*80)
    print(f"{'Metrik':<30} {'Model A (Utama)':<18} {'Model B (Pembanding)'}")
    print("-"*66)
    for k in ["accuracy", "precision_tepat_waktu", "recall_tepat_waktu", "f1_tepat_waktu",
              "precision_terlambat", "recall_terlambat", "f1_terlambat"]:
        print(f"{k:<30} {metadata_a['holdout_metrics'][k]:<18.4f} {metadata_b['holdout_metrics'][k]:.4f}")