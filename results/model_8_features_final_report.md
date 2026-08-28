# Final Evaluation Model 8 Features — GaussianNB

## 1. Tujuan

Eksperimen ini bertujuan untuk membandingkan performa model **GaussianNB** dengan **8 fitur** pada dua kondisi:

1. **Tanpa SMOTE** — data training asli tanpa oversampling
2. **Dengan SMOTE** — synthetic oversampling hanya pada data training

Kedua eksperimen menggunakan:
- **Tanpa scaler** (tidak ada StandardScaler/MinMaxScaler)
- **Stratified 10-Fold Cross Validation**
- **Holdout test 20%** dengan `random_state=42`
- **Algoritma:** GaussianNB

## 2. Dataset

| Item | Nilai |
|------|-------|
| Sumber | `iceberg.feature_store.training_dataset` + `iceberg.gold.dim_mahasiswa` |
| Total data | 13.181 |
| Training | 10.544 (80%) |
| Test | 2.637 (20%) |
| Jumlah kelas | 2 (Tepat Waktu, Terlambat) |
| Class imbalance ratio | 3.18:1 |

### Distribusi Target

| Kelas | Jumlah | Persentase |
|-------|--------|------------|
| Terlambat | 10.028 | 76.08% |
| Tepat Waktu | 3.153 | 23.92% |

### Distribusi Train/Test

| Set | Tepat Waktu | Terlambat | Total |
|-----|-------------|-----------|-------|
| Train | 2.522 | 8.022 | 10.544 |
| Test | 631 | 2.006 | 2.637 |

## 3. Fitur

| No | Nama Fitur | Tipe | Keterangan |
|----|------------|------|------------|
| 1 | jk_enc | int | Jenis kelamin (0=P, 1=L) |
| 2 | angkatan | int | Tahun masuk |
| 3 | ip | float | Indeks Prestasi |
| 4 | ipk | float | IP Kumulatif |
| 5 | total_sks | int | Total SKS yang diambil |
| 6 | jumlah_mk | int | Jumlah mata kuliah |
| 7 | sks_seharusnya | int |jumlah_mk × 24 |
| 8 | selisih_sks | int | total_sks − sks_seharusnya |

## 4. Konfigurasi Model

| Parameter | Nilai |
|-----------|-------|
| Algorithm | GaussianNB |
| Scaler | None |
| SMOTE | Yes/No |
| random_state | 42 |
| test_size | 20% |
| StratifiedKFold | 10 fold |
| shuffle | True |

## 5. Hasil 10-Fold Cross Validation

### 5.1 Tanpa SMOTE

| Fold | Accuracy | Precision | Recall | F1 |
|------|----------|-----------|--------|----|
| 1 | 0.7441 | 0.8759 | 0.7733 | 0.8214 |
| 2 | 0.7460 | 0.8690 | 0.7846 | 0.8246 |
| 3 | 0.7564 | 0.8738 | 0.7943 | 0.8321 |
| 4 | 0.7640 | 0.8762 | 0.8030 | 0.8380 |
| 5 | 0.7400 | 0.8667 | 0.7781 | 0.8200 |
| 6 | 0.7400 | 0.8729 | 0.7706 | 0.8185 |
| 7 | 0.7467 | 0.8773 | 0.7756 | 0.8233 |
| 8 | 0.7448 | 0.8707 | 0.7805 | 0.8231 |
| 9 | 0.7571 | 0.8845 | 0.7830 | 0.8307 |
| 10 | 0.7742 | 0.8939 | 0.7980 | 0.8432 |
| **Mean** | **0.7513** | **0.8761** | **0.7841** | **0.8275** |
| **Std** | **0.0107** | **0.0076** | **0.0104** | **0.0078** |

### 5.2 Dengan SMOTE

| Fold | Accuracy | Precision | Recall | F1 |
|------|----------|-----------|--------|----|
| 1 | 0.6692 | 0.9039 | 0.6326 | 0.7443 |
| 2 | 0.6796 | 0.9029 | 0.6488 | 0.7551 |
| 3 | 0.6796 | 0.9099 | 0.6421 | 0.7529 |
| 4 | 0.7052 | 0.9085 | 0.6808 | 0.7783 |
| 5 | 0.6708 | 0.9012 | 0.6372 | 0.7465 |
| 6 | 0.6793 | 0.9143 | 0.6384 | 0.7518 |
| 7 | 0.6964 | 0.9228 | 0.6559 | 0.7668 |
| 8 | 0.6917 | 0.9221 | 0.6496 | 0.7623 |
| 9 | 0.6926 | 0.9223 | 0.6509 | 0.7632 |
| 10 | 0.6983 | 0.9172 | 0.6633 | 0.7699 |
| **Mean** | **0.6863** | **0.9125** | **0.6500** | **0.7591** |
| **Std** | **0.0116** | **0.0080** | **0.0135** | **0.0103** |

## 6. Hasil Holdout Test

| Metrik | Tanpa SMOTE | Dengan SMOTE |
|--------|-------------|--------------|
| Accuracy | 0.7455 | 0.6864 |
| Precision | 0.8756 | 0.9190 |
| Recall | 0.7757 | 0.6446 |
| F1-Score | 0.8226 | 0.7577 |

## 7. Confusion Matrix

### 7.1 Tanpa SMOTE

| | Prediksi Tepat Waktu | Prediksi Terlambat |
|---|---|---|
| **Aktual Tepat Waktu** | 410 | 221 |
| **Aktual Terlambat** | 450 | 1.556 |

### 7.2 Dengan SMOTE

| | Prediksi Tepat Waktu | Prediksi Terlambat |
|---|---|---|
| **Aktual Tepat Waktu** | 517 | 114 |
| **Aktual Terlambat** | 713 | 1.293 |

## 8. Classification Report

### 8.1 Tanpa SMOTE

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Tepat Waktu | 0.48 | 0.65 | 0.55 | 631 |
| Terlambat | 0.88 | 0.78 | 0.82 | 2.006 |
| accuracy | | | 0.75 | 2.637 |
| weighted avg | 0.78 | 0.75 | 0.76 | 2.637 |

### 8.2 Dengan SMOTE

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Tepat Waktu | 0.42 | 0.82 | 0.56 | 631 |
| Terlambat | 0.92 | 0.64 | 0.76 | 2.006 |
| accuracy | | | 0.69 | 2.637 |
| weighted avg | 0.80 | 0.69 | 0.71 | 2.637 |

## 9. Perbandingan SMOTE vs Tanpa SMOTE

| Metrik | Tanpa SMOTE | Dengan SMOTE | Selisih |
|--------|-------------|--------------|---------|
| CV Accuracy Mean | 0.7513 | 0.6863 | -0.0650 |
| CV Accuracy Std | 0.0107 | 0.0116 | +0.0009 |
| CV Precision Mean | 0.8761 | 0.9125 | +0.0364 |
| CV Precision Std | 0.0076 | 0.0080 | +0.0004 |
| CV Recall Mean | 0.7841 | 0.6500 | -0.1341 |
| CV Recall Std | 0.0104 | 0.0135 | +0.0031 |
| CV F1 Mean | 0.8275 | 0.7591 | -0.0684 |
| CV F1 Std | 0.0078 | 0.0103 | +0.0025 |
| Test Accuracy | 0.7455 | 0.6864 | -0.0591 |
| Test Precision | 0.8756 | 0.9190 | +0.0434 |
| Test Recall | 0.7757 | 0.6446 | -0.1311 |
| Test F1 | 0.8226 | 0.7577 | -0.0649 |

### Distribusi SMOTE

| Kondisi | Tepat Waktu | Terlambat | Total |
|---------|-------------|-----------|-------|
| Sebelum SMOTE | 2.522 | 8.022 | 10.544 |
| Sesudah SMOTE | 8.022 | 8.022 | 16.044 |

## 10. Analisis

### Apakah SMOTE Meningkatkan Recall?

**Ya, secara parsial.** Recall untuk kelas **Tepat Waktu** meningkat dari 0.65 menjadi 0.82 (naik +0.17 pada holdout test). Artinya model dengan SMOTE lebih berhasil menemukan mahasiswa yang tepat waktu. Namun, recall untuk kelas **Terlambat** menurun dari 0.78 menjadi 0.64 (turun -0.14). Karena metrik recall yang dilaporkan adalah **macro average** (rata-rata kedua kelas), recall keseluruhan turun dari 0.7841 menjadi 0.6500.

### Apakah SMOTE Meningkatkan F1?

**Tidak.** F1-Score menurun dari 0.8275 (tanpa SMOTE) menjadi 0.7591 (dengan SMOTE) pada CV, dan dari 0.8226 menjadi 0.7577 pada holdout test. Penurunan ini disebabkan oleh penurunan recall yang lebih besar daripada peningkatan precision.

### Apakah Accuracy Meningkat/Menurun?

**Menurun signifikan.** Accuracy turun dari 0.7513 menjadi 0.6863 pada CV, dan dari 0.7455 menjadi 0.6864 pada holdout test. SMOTE mengurangi bias model terhadap kelas mayoritas (Terlambat), sehingga akurasi keseluruhan menurun.

### Bagaimana Perubahan Precision?

**Meningkat.** Precision naik dari 0.8761 menjadi 0.9125 pada CV, dan dari 0.8756 menjadi 0.9190 pada holdout test. Model dengan SMOTE lebih selektif dalam memprediksi kelas positif, mengurangi false positive.

### Bagaimana Stabilitas (Standard Deviation CV)?

Model tanpa SMOTE lebih stabil: std accuracy = 0.0107 vs 0.0116, std F1 = 0.0078 vs 0.0103. Perbedaan kecil menunjukkan kedua model cukup konsisten, namun tanpa SMOTE sedikit lebih stabil.

### Model Mana yang Lebih Baik?

**Tanpa SMOTE** lebih baik berdasarkan:
- **F1-Score** (0.8226 vs 0.7577) — metrik yang paling relevan untuk data tidak seimbang
- **Accuracy** (0.7455 vs 0.6864)
- **Recall keseluruhan** (0.7757 vs 0.6446)
- **Stabilitas CV** (std lebih rendah)

SMOTE hanya lebih baik pada **Precision** (0.9190 vs 0.8756), namun ini dikorbankan dengan penurunan recall yang besar.

## 11. Kesimpulan

Berdasarkan hasil eksperimen aktual:

1. **Model tanpa SMOTE** memberikan F1-Score **0.8226** pada holdout test, lebih tinggi 6.5 poin dibanding SMOTE (0.7577).

2. **SMOTE tidak efektif** untuk kasus ini. Meskipun recall kelas minoritas (Tepat Waktu) meningkat, recall kelas mayoritas (Terlambat) menurun lebih besar, sehingga F1 dan accuracy keseluruhan menurun.

3. **Ketidakseimbangan kelas** (76% vs 24%) menyebabkan model tanpa SMOTE cenderung memprediksi kelas mayoritas. Namun, ini sebenarnya menghasilkan F1 yang lebih baik karena F1 adalah harmonik mean precision dan recall.

4. **Model final yang direkomendasikan:** GaussianNB tanpa SMOTE dengan 8 fitur, menghasilkan:
   - CV Accuracy: 0.7513 ± 0.0107
   - CV F1: 0.8275 ± 0.0078
   - Test Accuracy: 0.7455
   - Test F1: 0.8226

## 12. Runtime

| Tahap | Waktu |
|-------|-------|
| Loading dataset | 14.68s |
| Preprocessing | 0.01s |
| CV tanpa SMOTE | 0.04s |
| CV dengan SMOTE | 0.12s |
| Training final tanpa SMOTE | 0.01s |
| Training final dengan SMOTE | 0.02s |
| Save models | 0.02s |
| Save datasets | 2.88s |
| **Total** | **17.8s** |

## 13. File Output

### Model
```
models/gaussian_nb_8_features/
├── without_smote/
│   ├── model.joblib
│   └── metadata.json
└── with_smote/
    ├── model.joblib
    └── metadata.json
```

### Dataset
```
data/model_8_features/
├── training_dataset_8_features.xlsx
├── train_dataset_8_features.xlsx
├── test_dataset_8_features.xlsx
├── smote_training_dataset_8_features.xlsx
├── cv_results_8_features.xlsx
├── evaluation_8_features.xlsx
├── confusion_matrix_8_features.xlsx
├── classification_report_8_features.xlsx
└── timings.json
```

### Report
```
results/model_8_features_final_report.md
```

## 14. Validasi

| Check | Status |
|-------|--------|
| 10-fold CV | PASS |
| No scaler | PASS |
| No data leakage | PASS |
| SMOTE only training folds | PASS |
| Model reload | PASS |
| Prediction test | PASS |
| Feature count = 8 | PASS |
| No old features | PASS |
