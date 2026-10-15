# Laporan Perbandingan Model: Model A (Utama) vs Model B (Pembanding)

## Ringkasan Eksekutif

| Aspek | Model A (Utama) | Model B (Pembanding) |
|-------|-----------------|----------------------|
| **Fitur Kategorikal** | jk_enc, angkatan_enc, ipk_kategori | jk_enc, angkatan_enc, ipk_kategori |
| **Fitur Numerik** | total_sks, jumlah_mk | selisih_sks, kecepatan_sks_per_semester |
| **Data Leakage** | Tidak (fitur bersih) | Ya (angkatan_enc, selisih_sks, kecepatan_sks_per_semester) |
| **Best Params** | weight_combo=8 (w_cat=0.9, w_gauss=0.1) | weight_combo=0 (w_cat=0.1, w_gauss=0.9) |
| **Bobot Total** | **1.0** ✓ | **1.0** ✓ |
| **Prediksi** | Argmax (probabilitas tertinggi) | Argmax (probabilitas tertinggi) |
| **CV F1 (5-fold)** | 0.9023 | 0.9964 |
| **Holdout Accuracy** | 0.8394 | 0.9945 |
| **Holdout F1** | 0.9060 | 0.9966 |
| **Holdout ROC-AUC** | 0.8177 | 0.9930 |
| **Prediksi Terlambat (Inference)** | 97.2% | 34.5% |

---

## 1. Desain Eksperimen

### 1.1 Data Training
- **Sumber**: `Data/data fix/training_dataset_full.xlsx` (15,505 baris)
- **Split**: 80% train (12,404) / 20% test (3,101) stratified by label
- **Label**: 0 = Tepat Waktu, 1 = Terlambat
- **Angkatan training**: 2012-2021 (lulus pakai label asli, aktif → label=1 Terlambat)

### 1.2 Data Inference
- **Sumber**: `Data/data fix/inference_dataset_full.xlsx` (12,338 baris)
- **Angkatan**: 2022, 2023, 2024 (aktif + lulus, tanpa label)

### 1.3 Model Architecture: Hybrid Naive Bayes
Menggabungkan dua Naive Bayes dengan bobot yang **harus menjumlahkan 1.0**:
- **CategoricalNB** untuk fitur kategorikal (bobot `w_cat`)
- **GaussianNB** untuk fitur numerik (bobot `w_gauss`)
- **Kontrain**: `w_cat + w_gauss = 1.0` (9 kombinasi: 0.1/0.9, 0.2/0.8, ..., 0.9/0.1)
- **Formula**: `proba_hybrid = w_cat * proba_cat + w_gauss * proba_gauss` (sudah dinormalisasi karena jumlah = 1)
- **Prediksi**: **Argmax** — kelas dengan probabilitas tertinggi

### 1.4 Grid Search
- **Kombinasi bobot**: 9 pasangan (w_cat + w_gauss = 1.0)
- **Parameter**: `weight_combo` (indeks 0-8 ke WEIGHT_GRID)
- **CV**: StratifiedKFold 5-fold
- **Scoring**: F1-score
- **Total fits**: 9 × 5 = 45 per model

---

## 2. Spesifikasi Fitur

### Model A (Utama) - Fitur Tanpa Leakage
| Kategori | Fitur | Deskripsi |
|----------|-------|-----------|
| Kategorikal | `jk_enc` | Jenis kelamin (0=Perempuan, 1=Laki-laki) |
| Kategorikal | `angkatan_enc` | Encoding angkatan |
| Kategorikal | `ipk_kategori` | 0=Rendah (<3.0), 1=Sedang (3.0-3.5), 2=Tinggi (>3.5) |
| Numerik | `total_sks` | Total SKS yang diambil |
| Numerik | `jumlah_mk` | Jumlah mata kuliah |

**Alasan pemilihan**: Menghindari data leakage dengan tidak menggunakan fitur yang bergantung pada status kelulusan (selisih_sks, kecepatan_sks_per_semester).

### Model B (Pembanding) - Fitur dengan Leakage
| Kategori | Fitur | Deskripsi |
|----------|-------|-----------|
| Kategorikal | `jk_enc` | Jenis kelamin (0=Perempuan, 1=Laki-laki) |
| Kategorikal | `angkatan_enc` | Encoding angkatan **(LEAKAGE)** |
| Kategorikal | `ipk_kategori` | Kategori IPK |
| Numerik | `selisih_sks` | Selisih SKS **(LEAKAGE - bergantung status lulus)** |
| Numerik | `kecepatan_sks_per_semester` | Kecepatan SKS/semester **(LEAKAGE)** |

**Catatan**: Model B menggunakan fitur yang tidak tersedia saat prediksi real-time untuk mahasiswa aktif.

---

## 3. Hasil Training & Validasi

### 3.1 WEIGHT_GRID (9 kombinasi, w_cat + w_gauss = 1.0)

| Index | w_cat | w_gauss |
|-------|-------|---------|
| 0 | 0.1 | 0.9 |
| 1 | 0.2 | 0.8 |
| 2 | 0.3 | 0.7 |
| 3 | 0.4 | 0.6 |
| 4 | 0.5 | 0.5 |
| 5 | 0.6 | 0.4 |
| 6 | 0.7 | 0.3 |
| 7 | 0.8 | 0.2 |
| 8 | 0.9 | 0.1 |

### 3.2 Best Parameters

| Model | weight_combo | w_cat | w_gauss | w_cat + w_gauss |
|-------|--------------|-------|---------|-----------------|
| **Model B** | 0 | 0.1 | 0.9 | **1.0** ✓ |
| **Model A** | 8 | 0.9 | 0.1 | **1.0** ✓ |

### 3.3 Holdout Test Set Metrics (3,101 sampel)

| Metrik | Model A (Utama) | Model B (Pembanding) |
|--------|-----------------|----------------------|
| Accuracy | **0.8394** | **0.9945** |
| Precision (Kelas 1) | 0.8541 | 0.9932 |
| Recall (Kelas 1) | 0.9646 | 1.0000 |
| F1-Score (Kelas 1) | 0.9060 | 0.9966 |
| ROC-AUC | 0.8177 | 0.9930 |

### 3.4 Confusion Matrix (Holdout)

#### Model A (Utama)
```
                 Predicted
                 TW    TL
Actual  TW      202   410
        TL       88  2401
```

#### Model B (Pembanding)
```
                 Predicted
                 TW    TL
Actual  TW      595    17
        TL        0  2489
```

---

## 4. Hasil Inference (12,338 mahasiswa angkatan 2022-2024)

### 4.1 Distribusi Prediksi (Argmax)

| Model | Tepat Waktu (0) | Terlambat (1) | % Terlambat |
|-------|-----------------|---------------|-------------|
| **Model A (Utama)** | 342 | 11,996 | **97.2%** |
| **Model B (Pembanding)** | 8,080 | 4,258 | **34.5%** |

---

## 5. Analisis & Interpretasi

### 5.1 Mengapa Model B "Terlalu Baik"?
Model B mencapai **Accuracy 99.5%** karena **data leakage**:
1. `selisih_sks` & `kecepatan_sks_per_semester` sangat korelasi dengan label
2. `angkatan_enc` memberi informasi temporal tidak tersedia untuk prediksi baru
3. **Konsekuensi**: Tidak bisa digunakan di produksi untuk mahasiswa aktif

### 5.2 Model A - Realistis tapi Perlu Perbaikan
- **Accuracy 83.9%** lebih realistis untuk deployment
- **Masalah**: 97.2% diprediksi Terlambat → terlalu pesimis (argmax cenderung memilih kelas mayoritas)
- **Penyebab**: Fitur `total_sks`, `jumlah_mk` tidak cukup diskriminatif
- **Recall kelas 0 (Tepat Waktu) hanya 33%** → banyak false negative

### 5.3 Rekomendasi
1. **Feature Engineering Model A**: Tambah fitur turunan (`ipk_trend`, `sks_per_semester_avg`)
2. **Class Weight / Resampling**: Handle imbalance (kelas 1 dominan 80% di training)
3. **Threshold Tuning**: Pertimbangkan threshold custom di atas argmax jika perlu keseimbangan
4. **Ensemble**: Gabungkan prediksi Model A + Model B dengan bobot

---

## 6. File Output

| File | Lokasi |
|------|--------|
| Model A | `models/model_a_utama.joblib` |
| Model A Metadata | `models/model_a_utama_metadata.json` |
| Model B | `models/model_b_pembanding.joblib` |
| Model B Metadata | `models/model_b_pembanding_metadata.json` |
| Inference A | `Data/data fix/inference_result_a.xlsx` |
| Inference B | `Data/data fix/inference_result_b.xlsx` |

---

## 7. Kolom Output Inference

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id_mahasiswa | string | NIM mahasiswa |
| IPK_kategori | int | 0=Rendah, 1=Sedang, 2=Tinggi |
| selisih_sks | int | Selisih SKS (Model B) / -1 (Model A) |
| jk_enc | int | 0=Perempuan, 1=Laki-laki |
| kecepatan_sks_per_semester | float | SKS/semester (Model B) / -1 (Model A) |
| total_sks | int | Total SKS (Model A) / -1 (Model B) |
| jumlah_mk | int | Jumlah MK (Model A) / -1 (Model B) |
| prob_tepat_waktu | float | Probabilitas kelas 0 |
| prob_terlambat | float | Probabilitas kelas 1 |
| prediksi | int | 0=Tepat Waktu, 1=Terlambat (argmax) |

---

## 8. Kesimpulan

| Kriteria | Model A (Utama) | Model B (Pembanding) |
|----------|-----------------|----------------------|
| **Validitas Metodologis** | ✅ Baik (no leakage) | ❌ Buruk (leakage) |
| **Bobot (w_cat + w_gauss)** | **1.0** ✓ | **1.0** ✓ |
| **Performa CV** | 0.9023 | 0.9964 |
| **Performa Holdout** | 0.8394 | 0.9945 |
| **Kelayakan Produksi** | ✅ Ya | ❌ Tidak |
| **Distribusi Prediksi** | Terlalu condong (97% TL) | Lebih seimbang (35% TL) |

**Rekomendasi**: Gunakan **Model A sebagai baseline**, lakukan feature engineering & handle imbalance. Model B hanya upper-bound teoritis.

---

*Generated: 2026-10-01 | Hybrid Naive Bayes + GridSearchCV (9 kombinasi w_cat+w_gauss=1) | Prediksi: Argmax*