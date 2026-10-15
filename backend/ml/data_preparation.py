import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

TRAINING_PATH = "/opt/airflow/data/data fix/training_dataset_full.xlsx"
INFERENCE_PATH = "/opt/airflow/data/data fix/inference_dataset_full.xlsx"

MODEL_A_CAT = ["angkatan_enc", "jk_enc", "ipk_kategori"]
MODEL_A_NUM = ["total_sks", "jumlah_mk"]

MODEL_B_CAT = ["angkatan_enc", "jk_enc", "ipk_kategori"]
MODEL_B_NUM = ["selisih_sks", "kecepatan_sks_per_semester"]

TARGET = "label"
ID_COL = "id_mahasiswa"

TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_training_excel():
    df = pd.read_excel(TRAINING_PATH)
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    return df


def load_inference_excel():
    df = pd.read_excel(INFERENCE_PATH)
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    return df


def prepare_model_data(df, cat_cols, num_cols):
    X = df[cat_cols + num_cols].copy()
    y = df[TARGET].copy()
    return X, y


def stratified_train_test_split(X, y):
    return train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )


def get_model_a_data():
    df = load_training_excel()
    X, y = prepare_model_data(df, MODEL_A_CAT, MODEL_A_NUM)
    X_train, X_test, y_train, y_test = stratified_train_test_split(X, y)
    return X_train, X_test, y_train, y_test


def get_model_b_data():
    df = load_training_excel()
    X, y = prepare_model_data(df, MODEL_B_CAT, MODEL_B_NUM)
    X_train, X_test, y_train, y_test = stratified_train_test_split(X, y)
    return X_train, X_test, y_train, y_test


def get_inference_data(model="A"):
    df = load_inference_excel()
    if model == "B":
        cat_cols, num_cols = MODEL_B_CAT, MODEL_B_NUM
    else:
        cat_cols, num_cols = MODEL_A_CAT, MODEL_A_NUM
    X = df[cat_cols + num_cols].copy()
    ids = df[ID_COL].values
    return X, ids, df


def get_feature_config(model="A"):
    if model == "B":
        cat, num = MODEL_B_CAT, MODEL_B_NUM
    else:
        cat, num = MODEL_A_CAT, MODEL_A_NUM
    return {
        "categorical": cat,
        "numerical": num,
        "target": TARGET,
        "id_col": ID_COL,
        "all_features": cat + num,
    }


if __name__ == "__main__":
    X_tr, X_te, y_tr, y_te = get_model_a_data()
    print(f"Train: {X_tr.shape}, Test: {X_te.shape}")
    print(f"Train label dist:\n{y_tr.value_counts().sort_index()}")
    print(f"Test label dist:\n{y_te.value_counts().sort_index()}")
    print(f"Features: {get_feature_config()}")