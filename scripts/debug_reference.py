import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.naive_bayes import CategoricalNB, GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

# Load EXACT same way as reference
df_training = pd.read_excel("/opt/airflow/Data/data fix/training_dataset_full.xlsx")
df_inference = pd.read_excel("/opt/airflow/Data/data fix/inference_dataset_full.xlsx")

print("Training:", df_training.shape)
print("Inference:", df_inference.shape)

# EXACT features from reference
CATEGORICAL_FEATURES = ["angkatan_enc", "jk_enc", "ipk_kategori"]
NUMERICAL_FEATURES = ["total_sks", "jumlah_mk"]
TARGET = "label"

fitur_model = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

X = df_training[fitur_model].copy()
y = df_training[TARGET].copy()

print("\nJumlah data:", len(X))
print("Jumlah fitur:", len(fitur_model))

# EXACT split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print("\nDATA TRAINING:", len(X_train))
print("Tepat Waktu (0):", (y_train == 0).sum())
print("Terlambat (1):", (y_train == 1).sum())

print("\nDATA TESTING:", len(X_test))
print("Tepat Waktu (0):", (y_test == 0).sum())
print("Terlambat (1):", (y_test == 1).sum())

# Separate categorical & numerical EXACTLY like reference
X_train_cat = X_train[CATEGORICAL_FEATURES].copy()
X_test_cat = X_test[CATEGORICAL_FEATURES].copy()
X_train_num = X_train[NUMERICAL_FEATURES].copy()
X_test_num = X_test[NUMERICAL_FEATURES].copy()

# Convert types
X_train_cat = X_train_cat.astype(int)
X_test_cat = X_test_cat.astype(int)
X_train_num = X_train_num.astype(float)
X_test_num = X_test_num.astype(float)

print("\nTrain cat shape:", X_train_cat.shape)
print("Train num shape:", X_train_num.shape)

# Hybrid NB class from reference
class HybridNaiveBayes:
    def __init__(self, weight_cat, weight_gauss):
        self.weight_cat = weight_cat
        self.weight_gauss = weight_gauss
        self.categorical_model = CategoricalNB()
        self.gaussian_model = GaussianNB()

    def fit(self, X_cat, X_num, y):
        self.categorical_model.fit(X_cat, y)
        self.gaussian_model.fit(X_num, y)
        self.classes_ = self.categorical_model.classes_
        return self

    def predict_proba(self, X_cat, X_num):
        cat_log_proba = self.categorical_model.predict_log_proba(X_cat)
        gauss_log_proba = self.gaussian_model.predict_log_proba(X_num)
        combined_log_proba = (
            self.weight_cat * cat_log_proba + self.weight_gauss * gauss_log_proba
        )
        max_log = np.max(combined_log_proba, axis=1, keepdims=True)
        exp_proba = np.exp(combined_log_proba - max_log)
        probabilities = exp_proba / exp_proba.sum(axis=1, keepdims=True)
        return probabilities

    def predict(self, X_cat, X_num):
        probabilities = self.predict_proba(X_cat, X_num)
        return self.classes_[np.argmax(probabilities, axis=1)]

# Manual hitung metrik
def hitung_metrik_manual(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

# EXACT optimization from reference
weights = np.arange(0.1, 1.0, 0.1)
num_classes = len(np.unique(y_train))
skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

print("\nOPTIMASI BOBOT (EXACT REFERENCE)")

for weight_cat in weights:
    weight_cat = round(float(weight_cat), 1)
    weight_gauss = round(1.0 - weight_cat, 1)
    
    print(f"\nMenguji bobot: Cat={weight_cat:.1f}, Gauss={weight_gauss:.1f}")
    
    oof_probabilities = np.zeros((len(X_train), num_classes))
    
    for fold, (train_idx, valid_idx) in enumerate(skf.split(X_train, y_train), start=1):
        X_fold_train_cat = X_train_cat.iloc[train_idx]
        X_fold_train_num = X_train_num.iloc[train_idx]
        y_fold_train = y_train.iloc[train_idx]
        
        X_fold_valid_cat = X_train_cat.iloc[valid_idx]
        X_fold_valid_num = X_train_num.iloc[valid_idx]
        y_fold_valid = y_train.iloc[valid_idx]
        
        fold_model = HybridNaiveBayes(weight_cat=weight_cat, weight_gauss=weight_gauss)
        fold_model.fit(X_fold_train_cat, X_fold_train_num, y_fold_train)
        
        fold_probabilities = fold_model.predict_proba(X_fold_valid_cat, X_fold_valid_num)
        oof_probabilities[valid_idx] = fold_probabilities
    
    predictions = np.argmax(oof_probabilities, axis=1)
    
    # METRIK
    precision_tepat = precision_score(y_train, predictions, pos_label=0, zero_division=0)
    recall_tepat = recall_score(y_train, predictions, pos_label=0, zero_division=0)
    f1_tepat = f1_score(y_train, predictions, pos_label=0, zero_division=0)
    
    precision_terlambat = precision_score(y_train, predictions, pos_label=1, zero_division=0)
    recall_terlambat = recall_score(y_train, predictions, pos_label=1, zero_division=0)
    f1_terlambat = f1_score(y_train, predictions, pos_label=1, zero_division=0)
    
    accuracy = accuracy_score(y_train, predictions)
    
    print(f"  F1 Tepat: {f1_tepat:.4f}, Recall Tepat: {recall_tepat:.4f}, Prec Tepat: {precision_tepat:.4f}")
    print(f"  F1 Terlambat: {f1_terlambat:.4f}, Acc: {accuracy:.4f}")

print("\n=== DONE ===")