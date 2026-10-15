import os
os.environ['PYSPARK_PYTHON'] = '/usr/bin/python3'
os.environ['PYSPARK_DRIVER_PYTHON'] = '/usr/bin/python3'

import numpy as np
import pandas as pd
import joblib
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from train import HybridNaiveBayes

MODEL_DIR = Path("/opt/airflow/models")
OUTPUT_DIR = Path("/opt/airflow/Data/data fix")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_model(model_name):
    model_path = MODEL_DIR / f"{model_name}.joblib"
    meta_path = MODEL_DIR / f"{model_name}_metadata.json"
    model = joblib.load(model_path)
    with open(meta_path) as f:
        metadata = json.load(f)
    return model, metadata


def run_inference_and_save_gold(model_name="model_a_utama"):
    print(f"\n{'='*60}")
    print(f"Inference & Gold Layer Save: {model_name}")
    print(f"{'='*60}")

    model, metadata = load_model(model_name)
    cat_cols = metadata["categorical_features"]
    num_cols = metadata["numerical_features"]

    from data_preparation import load_inference_excel

    df = load_inference_excel()
    X = df[cat_cols + num_cols].copy()
    ids = df["id_mahasiswa"].values

    print(f"Input shape: {X.shape}")
    print(f"Categorical: {cat_cols}")
    print(f"Numerical: {num_cols}")

    X_cat = X[cat_cols].astype(int).values
    X_num = X[num_cols].astype(float).values

    inference_probabilities = model.predict_proba(X_cat, X_num)
    label_prediksi = model.predict(X_cat, X_num)

    results_df = pd.DataFrame({
        "id_mahasiswa": ids,
        "angkatan": df["angkatan"].values,
        "angkatan_enc": df["angkatan_enc"].values,
        "jk_enc": df["jk_enc"].values,
        "ipk_kategori": df["ipk_kategori"].values,
        "total_sks": df["total_sks"].values,
        "jumlah_mk": df["jumlah_mk"].values,
        "selisih_sks": df["selisih_sks"].values,
        "kecepatan_sks_per_semester": df["kecepatan_sks_per_semester"].values,
        "prob_tepat_waktu": inference_probabilities[:, 0],
        "prob_terlambat": inference_probabilities[:, 1],
        "prediksi": label_prediksi.astype(int),
        "prediksi_label": np.where(label_prediksi == 1, "Terlambat", "Tepat Waktu")
    })

    print(f"\nJumlah data inference: {len(results_df)}")
    print("\nDistribusi prediksi:")
    print(results_df["prediksi_label"].value_counts())

    # Save to Excel
    output_path = OUTPUT_DIR / f"inference_result_{model_name}.xlsx"
    results_df.to_excel(output_path, index=False)
    print(f"Saved to Excel: {output_path}")

    # Save to Iceberg Gold Layer via Spark with proper Python path
    print("\n" + "="*60)
    print("SAVING TO GOLD LAYER (ICEBERG)")
    print("="*60)
    
    from backend.spark.session import get_spark
    spark = get_spark(f"Inference Gold Layer - {model_name}")
    
    # Set Python path for executors
    spark.sparkContext._conf.set("spark.executorEnv.PYSPARK_PYTHON", "/usr/bin/python3")
    spark.sparkContext._conf.set("spark.executorEnv.PYSPARK_DRIVER_PYTHON", "/usr/bin/python3")
    spark.sparkContext._conf.set("spark.python.worker.python", "/usr/bin/python3")
    
    # Convert to Spark DataFrame
    spark_df = spark.createDataFrame(results_df)
    
    # Write to Gold layer as Iceberg table
    gold_table = "hive_iceberg.gold.inference_result_model_utama"
    
    # Drop table if exists and recreate
    spark.sql(f"DROP TABLE IF EXISTS {gold_table}")
    
    spark_df.writeTo(gold_table) \
        .tableProperty("write.format.default", "parquet") \
        .tableProperty("write.parquet.compression-codec", "zstd") \
        .partitionedBy("angkatan") \
        .createOrReplace()
    
    print(f"Saved to Iceberg Gold table: {gold_table}")
    
    # Verify
    count = spark.sql(f"SELECT COUNT(*) FROM {gold_table}").collect()[0][0]
    print(f"Verified row count in Gold: {count}")
    
    # Show sample
    spark.sql(f"SELECT * FROM {gold_table} LIMIT 5").show(truncate=False)
    
    # Distribution per angkatan
    print("\nDistribusi per angkatan di Gold:")
    spark.sql(f"""
        SELECT angkatan, prediksi_label, COUNT(*) as jumlah
        FROM {gold_table}
        GROUP BY angkatan, prediksi_label
        ORDER BY angkatan, prediksi_label
    """).show(truncate=False)
    
    spark.stop()
    
    return results_df


if __name__ == "__main__":
    run_inference_and_save_gold("model_a_utama")