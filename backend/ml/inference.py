import numpy as np
import pandas as pd
import joblib
import json
import warnings
import sys
from pathlib import Path

warnings.filterwarnings("ignore")

# Ensure backend/ml is in Python path
ML_DIR = Path(__file__).parent
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

from hybrid_nb import HybridNaiveBayes

from backend.config.namespaces import model_dir, ml_output_dir


def load_model(model_name, model_dir_path=None):
    base_dir = Path(model_dir_path) if model_dir_path is not None else model_dir()
    model_path = base_dir / f"{model_name}.joblib"
    meta_path = base_dir / f"{model_name}_metadata.json"
    model = joblib.load(model_path)
    with open(meta_path) as f:
        metadata = json.load(f)
    return model, metadata


def run_inference(
    model_name="model_a_utama",
    data_loader=None,
    output_dir_path=None,
    output_filename=None,
):
    print(f"\n{'='*60}")
    print(f"Inference: {model_name}")
    print(f"{'='*60}")

    model, metadata = load_model(model_name)
    cat_cols = metadata["categorical_features"]
    num_cols = metadata["numerical_features"]

    # Sumber data: default Excel (perilaku produksi). Jalur QA dapat
    # menyuntikkan ``data_loader`` yang membaca Feature Store QA.
    if data_loader is None:
        from data_preparation import get_inference_data

        X, ids, df_inference = get_inference_data(model="A")
    else:
        X, ids, df_inference = data_loader()

    print(f"Input shape: {X.shape}")
    print(f"Categorical features: {cat_cols}")
    print(f"Numerical features: {num_cols}")

    X_cat = X[cat_cols].astype(int).values
    X_num = X[num_cols].astype(float).values

    # Predict using the trained Hybrid Naive Bayes model
    inference_probabilities = model.predict_proba(X_cat, X_num)
    label_prediksi = model.predict(X_cat, X_num)

    # Validate probabilities sum to 1
    prob_sum = inference_probabilities[:, 0] + inference_probabilities[:, 1]
    assert np.allclose(prob_sum, 1.0), "Probabilities don't sum to 1"

    # Create result dataframe with required columns
    result_df = pd.DataFrame({
        "id_mahasiswa": ids,
        "IPK_kategori": df_inference["ipk_kategori"].values,
        "selisih_sks": df_inference["selisih_sks"].values if "selisih_sks" in df_inference.columns else -1,
        "jk_enc": df_inference["jk_enc"].values,
        "kecepatan_sks_per_semester": df_inference["kecepatan_sks_per_semester"].values if "kecepatan_sks_per_semester" in df_inference.columns else -1,
        "prob_tepat_waktu": inference_probabilities[:, 0],
        "prob_terlambat": inference_probabilities[:, 1],
        "prediksi": label_prediksi.astype(int)  # 0 = Tepat Waktu, 1 = Terlambat
    })

    print(f"\nJumlah data inference: {len(result_df)}")
    print(f"Input rows: {len(X)}, Output rows: {len(result_df)}")
    assert len(X) == len(result_df), "Input rows != Output rows"

    print("\nDistribusi hasil prediksi:")
    pred_dist = result_df["prediksi"].value_counts().sort_index()
    print(pred_dist)
    print(f"Tepat Waktu (0): {pred_dist.get(0, 0)} ({(pred_dist.get(0, 0)/len(result_df)*100):.1f}%)")
    print(f"Terlambat (1): {pred_dist.get(1, 0)} ({(pred_dist.get(1, 0)/len(result_df)*100):.1f}%)")

    # Validate probabilities sum to 1
    prob_sum = result_df["prob_tepat_waktu"] + result_df["prob_terlambat"]
    print(f"\nProbabilitas Tepat Waktu + Terlambat = 1 check:")
    print(f"  Min: {prob_sum.min():.10f}, Max: {prob_sum.max():.10f}")
    assert np.allclose(prob_sum, 1.0), "Probabilities don't sum to 1"

    # Check missing values in model features
    print("\nMissing value check on model features:")
    model_features = ["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk"]
    for col in model_features:
        if col in df_inference.columns:
            missing = df_inference[col].isnull().sum()
            if missing > 0:
                print(f"  WARNING: {col} has {missing} missing values")
            else:
                print(f"  OK: {col} - no missing values")

    # Data types check
    print("\nData types:")
    print(result_df.dtypes)

    # Show 10 sample predictions
    print("\n10 Contoh hasil inference:")
    display_cols = ["id_mahasiswa", "IPK_kategori", "selisih_sks", "jk_enc", 
                    "kecepatan_sks_per_semester", "prob_tepat_waktu", "prob_terlambat", "prediksi"]
    print(result_df[display_cols].head(10).to_string())

    # Save to Excel (direktori mengikuti PIPELINE_ML_OUTPUT_DIR)
    out_dir = Path(output_dir_path) if output_dir_path is not None else ml_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = output_filename or "inference_result_model_a_utama.xlsx"
    output_path = out_dir / filename
    result_df.to_excel(output_path, index=False)
    print(f"\nSaved to {output_path}")

    return result_df


if __name__ == "__main__":
    print("="*80)
    print("RUNNING INFERENCE FOR MODEL UTAMA (Model A)")
    print("="*80)

    run_inference("model_a_utama")