# Hasil Machine Learning

> **Proyek:** Sistem Lakehouse untuk Prediksi Tingkat Kelulusan Mahasiswa  
> **Versi Model:** v4.0.0  
> **Tanggal Training:** 2026-09-02  
> **Status:** Pipeline End-to-End Berhasil (Smoke Test PASS)

---

## 1. Ringkasan

Dokumentasi ini merekam hasil implementasi model Machine Learning untuk prediksi status kelulusan mahasiswa pada Sistem Data Lakehouse. Model dibangun menggunakan algoritma **Gaussian Naive Bayes** dengan dua varian eksperimen: tanpa SMOTE dan dengan SMOTE.

### Tujuan Model
- Memprediksi apakah mahasiswa akan lulus tepat waktu atau terlambat
- Kelas prediksi: **Tepat Waktu** (label=0) dan **Terlambat** (label=1)
- Data training berasal dari Feature Store yang sudah melalui proses Silver → Gold
- Inference digunakan untuk mahasiswa aktif tahun 2022-2024 sebagai objek prediksi

### Hubungan ML dengan Lakehouse

```
Bronze → Silver → Gold → Feature Store → ML Training → Inference → Iceberg → Trino/Superset
```

Pipeline Machine Learning merupakan tahap 5 dan 6 dalam arsitektur Lakehouse:
- **Tahap 5 (ML Training):** Membaca training dataset dari Feature Store, melakukan validasi, training model, dan menyimpan artifact ke Model Registry
- **Tahap 6 (Inference):** Membaca inference dataset dari Feature Store, memuat model dari Model Registry, melakukan prediksi, dan menyimpan hasil prediksi

---

## 2. Dataset Machine Learning

### 2.1 Sumber Data

| Komponen | Nilai |
|---|---|
| Jumlah data Gold | 32.703 mahasiswa |
| Data training (LULUS dengan label) | 15.599 baris |
| Data inference (AKTIF 2022-2024) | 12.501 baris |
| Jumlah fitur | 8 fitur |
| Target | `label` (integer: 0 atau 1) |
| Kelas | 0 = Tepat Waktu, 1 = Terlambat |
| Identifier | `id_mahasiswa` |

### 2.2 Distribusi Kelas pada Data Training

| Label | Kelas | Jumlah | Persentase |
|---|---|---:|---:|
| 0 | Tepat Waktu | 3.153 | 20,21% |
| 1 | Terlambat | 12.446 | 79,79% |
| **Total** | | **15.599** | **100%** |

**Catatan Penting:** Dataset memiliki ketidakseimbangan kelas yang signifikan, di mana kelas Terlambat (1) lebih dominan dengan proporsi hampir 4x lipat dari kelas Tepat Waktu (0).

### 2.3 Distribusi Kelas pada Data Inference

| Angkatan | Semester | Target SKS | Jumlah Mahasiswa |
|---|---|---|---:|
| 2022 | 7 | 135 | 4.109 |
| 2023 | 5 | 95 | 4.046 |
| 2024 | 3 | 55 | 4.346 |
| **Total** | | | **12.501** |

---

## 3. Fitur Model

### 3.1 Daftar Fitur

Model menggunakan **8 fitur** yang diambil dari Gold `dim_mahasiswa`:

| No | Nama Fitur | Tipe | Deskripsi |
|---|---|---|---|
| 1 | `jk_enc` | Integer | Encoding jenis kelamin: 0 = Perempuan, 1 = Laki-laki |
| 2 | `angkatan` | Integer | Tahun masuk mahasiswa |
| 3 | `ip` | Double | Indeks Prestasi semester terakhir |
| 4 | `ipk` | Double | Indeks Prestasi Kumulatif (IPK) |
| 5 | `total_sks` | Integer | Total SKS yang sudah ditempuh |
| 6 | `jumlah_mk` | Integer | Jumlah mata kuliah yang sudah ditempuh |
| 7 | `sks_seharusnya` | Integer | Target SKS berdasarkan semester aktif (snapshot 2026) |
| 8 | `selisih_sks` | Integer | Selisih antara `total_sks` - `sks_seharusnya` |

### 3.2 Detail Encoding Jenis Kelamin

Proses encoding dilakukan di `feature_engineering.py` menggunakan PySpark:

```
P / PEREMPUAN → 0
L / LAKI-LAKI / LAKI LAKI → 1
```

### 3.3 Perhitungan Target SKS (sks_seharusnya)

Target SKS menggunakan mapping berikut berdasarkan snapshot 2026:

| Semester | Target SKS |
|---|---|
| 1 | 17 |
| 2 | 36 |
| 3 | 55 |
| 4 | 75 |
| 5 | 95 |
| 6 | 115 |
| 7 | 135 |
| 8 | 144 |

### 3.4 Fitur Terlarang (Forbidden Features)

Kolom berikut **TIDAK BOLEH** masuk sebagai fitur model (data leakage):

| Kolom | Alasan |
|---|---|
| `jenis_kelamin` | Digunakan untuk membuat `jk_enc`, bukan fitur langsung |
| `tanggal_masuk` | Metadata, bukan fitur numerik |
| `tanggal_keluar` | Metadata, bukan fitur numerik |
| `status_mahasiswa` | Mengandung informasi target |
| `lama_studi` | Mengandung informasi target (hanya dihitung untuk LULUS) |
| `status_kelulusan` | Mengandung informasi target |
| `label` | Target variable, bukan fitur |

### 3.5 Pembedaan Kolom

**Penting untuk dipahami:**

| Layer | Kolom | Keterangan |
|---|---|---|
| **Gold dim_mahasiswa** | `id_mahasiswa`, `jenis_kelamin`, `tanggal_masuk`, `tanggal_keluar`, `ipk`, `total_sks`, `jumlah_mk`, `status_mahasiswa`, `angkatan`, `semester`, `ip`, `sks_seharusnya`, `selisih_sks`, `lama_studi`, `status_kelulusan`, `label` | 16 kolom (wide schema) |
| **Feature Store (preprocessed)** | `id_mahasiswa`, `jk_enc`, `angkatan`, `ip`, `ipk`, `total_sks`, `jumlah_mk`, `sks_seharusnya`, `selisih_sks`, `label` | Kolom hasil encoding |
| **Model Input (X)** | `jk_enc`, `angkatan`, `ip`, `ipk`, `total_sks`, `jumlah_mk`, `sks_seharusnya`, `selisih_sks` | 8 fitur |

---

## 4. Persiapan Data

### 4.1 Preprocessing yang Digunakan

| Langkah | Status | Keterangan |
|---|---|---|
| Encoding jenis kelamin | ✅ Digunakan | `jk_enc` dibuat dari `jenis_kelamin` menggunakan PySpark |
| Pemilihan feature | ✅ Digunakan | 8 fitur dipilih sesuai baseline |
| Handling missing value | ❌ Tidak dilakukan | Data NULL difilter di Feature Store (tidak diimputasi) |
| Scaling | ❌ Tidak digunakan | Feature X mentah langsung dimasukkan ke GaussianNB |
| Train-test split | ✅ Digunakan | 80% train, 20% test, stratified |
| Stratified split | ✅ Digunakan | `stratify=y` pada `train_test_split` |
| SMOTE | ✅ Digunakan (varian B) | Hanya pada training fold (bukan test) |
| StandardScaler | ❌ Tidak digunakan | Sesuai revisi Tahap 3 |

### 4.2 Alur Persiapan Data

```
1. Baca training_dataset dari Feature Store
2. Leakage check (forbidden features)
3. Build target encoding: label 0→0, 1→1
4. Build feature matrix X (8 fitur) dari pandas DataFrame
5. Train-test split: 80% development, 20% holdout test
   - Stratified berdasarkan label
   - random_state = 42
6. Cross-validation pada development set (80%)
7. Holdout evaluation pada test set (20%)
8. Fit final estimator pada seluruh data
```

### 4.3 Detail SMOTE (Varian B)

Pada varian dengan SMOTE, oversampling dilakukan **DI DALAM** pipeline menggunakan `imblearn.pipeline.Pipeline`:

```python
ImbPipeline([
    ("smote", SMOTE(random_state=42)),
    ("model", GaussianNB()),
])
```

**Penting:** SMOTE hanya di-apply pada training fold saat cross-validation, **TIDAK** menyentuh validation/test fold. Hal ini mencegah data leakage.

---

## 5. Model Machine Learning

### 5.1 Gaussian Naive Bayes

| Komponen | Nilai |
|---|---|
| Nama Model | `gaussian_nb_lulusan` |
| Versi | v4.0.0 |
| Tipe | GaussianNB |
| Algoritma | Naive Bayes dengan asumsi distribusi Gaussian |
| Parameter Default | Semua parameter sklearn GaussianNB default |
| Random State | 42 (untuk reproducibility) |

### 5.2 Varian Eksperimen

| Varian | SMOTE | Keterangan |
|---|---|---|
| **without_smote** (Model A) | ❌ | GaussianNB langsung, tanpa oversampling |
| **with_smote** (Model B) | ✅ | SMOTE oversampling + GaussianNB |

### 5.3 Arsitektur Pipeline

```
Input (8 features)
    │
    ├─ [Tanpa SMOTE] → GaussianNB() → Prediksi
    │
    └─ [Dengan SMOTE] → SMOTE(random_state=42) → GaussianNB() → Prediksi
```

---

## 6. Pembagian Data Training dan Testing

### 6.1 Konfigurasi Split

| Parameter | Nilai |
|---|---|
| Test Size | 0.20 (20%) |
| Random State | 42 |
| Stratification | Ya (berdasarkan label) |

### 6.2 Jumlah Data

| Set | Jumlah | Persentase |
|---|---:|---:|
| Development (training) | 12.479 | 80% |
| Holdout test | 3.120 | 20% |
| **Total** | **15.599** | **100%** |

### 6.3 Cross Validation

| Parameter | Nilai |
|---|---|
| Jenis | StratifiedKFold |
| Jumlah Fold | 10 |
| Shuffle | True |
| Random State | 42 |
| Scoring | Accuracy, Precision, Recall, F1 (pos_label=1) |

### 6.4 Hasil Cross Validation (Tanpa SMOTE)

| Fold | Accuracy | Precision | Recall | F1 Score |
|---|---:|---:|---:|---:|
| 1 | 0.7292 | 0.9229 | 0.7209 | 0.8095 |
| 2 | 0.7372 | 0.9326 | 0.7229 | 0.8145 |
| 3 | 0.7019 | 0.9216 | 0.6847 | 0.7857 |
| 4 | 0.7075 | 0.9135 | 0.6998 | 0.7925 |
| 5 | 0.7236 | 0.9200 | 0.7159 | 0.8052 |
| 6 | 0.7300 | 0.9296 | 0.7159 | 0.8088 |
| 7 | 0.7147 | 0.9267 | 0.6978 | 0.7961 |
| 8 | 0.7356 | 0.9301 | 0.7226 | 0.8133 |
| 9 | 0.7155 | 0.9178 | 0.7065 | 0.7984 |
| 10 | 0.7049 | 0.9265 | 0.6844 | 0.7873 |

### 6.5 Hasil Cross Validation (Dengan SMOTE)

| Fold | Accuracy | Precision | Recall | F1 Score |
|---|---:|---:|---:|---:|
| 1 | 0.6779 | 0.9473 | 0.6315 | 0.7578 |
| 2 | 0.6811 | 0.9530 | 0.6315 | 0.7597 |
| 3 | 0.6562 | 0.9437 | 0.6054 | 0.7376 |
| 4 | 0.6635 | 0.9337 | 0.6225 | 0.7470 |
| 5 | 0.6635 | 0.9364 | 0.6205 | 0.7464 |
| 6 | 0.6715 | 0.9508 | 0.6205 | 0.7509 |
| 7 | 0.6683 | 0.9533 | 0.6145 | 0.7473 |
| 8 | 0.6771 | 0.9554 | 0.6241 | 0.7550 |
| 9 | 0.6458 | 0.9382 | 0.5950 | 0.7282 |
| 10 | 0.6439 | 0.9436 | 0.5889 | 0.7252 |

---

## 7. Hasil Evaluasi Model

### 7.1 Ringkasan Perbandingan

| Metrik | Tanpa SMOTE (Mean ± Std) | Dengan SMOTE (Mean ± Std) | Pemenang |
|---|---|---|---|
| CV Accuracy | 0.7200 ± 0.0122 | 0.6649 ± 0.0123 | Tanpa SMOTE |
| CV Precision | 0.9241 ± 0.0057 | 0.9455 ± 0.0073 | Dengan SMOTE |
| CV Recall | 0.7071 ± 0.0141 | 0.6154 ± 0.0138 | Tanpa SMOTE |
| **CV F1 Score** | **0.8011 ± 0.0100** | **0.7455 ± 0.0112** | **Tanpa SMOTE** |

### 7.2 Hasil Holdout Test

| Metrik | Tanpa SMOTE | Dengan SMOTE | Pemenang |
|---|---:|---:|---|
| Accuracy | 0.7308 | 0.6785 | Tanpa SMOTE |
| Precision | 0.9243 | 0.9471 | Dengan SMOTE |
| Recall | 0.7216 | 0.6324 | Tanpa SMOTE |
| **F1 Score** | **0.8105** | **0.7584** | **Tanpa SMOTE** |

### 7.3 Confusion Matrix

#### Tanpa SMOTE (Holdout Test)

| Actual \ Predicted | Tepat Waktu (0) | Terlambat (1) |
|---|---:|---:|
| **Tepat Waktu (0)** | 484 | 147 |
| **Terlambat (1)** | 693 | 1.796 |

#### Dengan SMOTE (Holdout Test)

| Actual \ Predicted | Tepat Waktu (0) | Terlambat (1) |
|---|---:|---:|
| **Tepat Waktu (0)** | 543 | 88 |
| **Terlambat (1)** | 915 | 1.574 |

### 7.4 Classification Report (Tanpa SMOTE)

```
              precision    recall  f1-score   support

 Tepat Waktu     0.4112    0.7670    0.5354       631
   Terlambat     0.9243    0.7216    0.8105      2489

    accuracy                         0.7308      3120
   macro avg     0.6678    0.7443    0.6729      3120
weighted avg     0.8206    0.7308    0.7548      3120
```

### 7.5 Classification Report (Dengan SMOTE)

```
              precision    recall  f1-score   support

 Tepat Waktu     0.3724    0.8605    0.5199       631
   Terlambat     0.9471    0.6324    0.7584      2489

    accuracy                         0.6785      3120
   macro avg     0.6597    0.7465    0.6391      3120
weighted avg     0.8308    0.6785    0.7101      3120
```

---

## 8. Perbandingan SMOTE

### 8.1 Analisis

Berdasarkan hasil evaluasi aktual dari artifact training, **model tanpa SMOTE memiliki performa lebih baik** pada metrik utama:

| Perubahan | Tanpa SMOTE | Dengan SMOTE | Selisih |
|---|---:|---:|---:|
| F1 Score (CV) | 0.8011 | 0.7455 | **-0.0556** |
| F1 Score (Holdout) | 0.8105 | 0.7584 | **-0.0521** |
| Recall (CV) | 0.7071 | 0.6154 | **-0.0917** |
| Recall (Holdout) | 0.7216 | 0.6324 | **-0.0892** |

### 8.2 Kesimpulan

1. **F1 Score lebih rendah pada SMOTE**: Penggunaan SMOTE justru **menurunkan** F1 Score dari 0.8011 menjadi 0.7455 (penurunan ~6.9%)

2. **Recall menurun signifikan**: Recall (kemampuan mendeteksi kelas Terlambat) menurun dari 0.7071 menjadi 0.6154 (penurunan ~12.9%)

3. **Precision meningkat sedikit**: Precision naik dari 0.9241 menjadi 0.9455 (peningkatan ~2.3%), namun tidak cukup untuk mengimbangi penurunan Recall

4. **Akurasi menurun**: Akurasi turun dari 0.7200 menjadi 0.6649

### 8.3 Penjelasan

Meskipun dataset memiliki ketidakseimbangan kelas, SMOTE tidak selalu menghasilkan performa lebih baik karena:

1. GaussianNB sudah cukup robust terhadap ketidakseimbangan kelas
2. SMOTE dapat menambah noise pada data training, terutama pada boundary decision
3. Recall yang menurun pada kelas Terlambat menunjukkan SMOTE membuat model lebih sulit mendeteksi mahasiswa yang benar-benar terlambat

---

## 9. Model Terpilih

### 9.1 Identifikasi Model

Berdasarkan hasil evaluasi, **model terpilih adalah GaussianNB tanpa SMOTE** (varian without_smote).

| Komponen | Nilai |
|---|---|
| Model Name | `gaussian_nb_lulusan` |
| Model Version | v4.0.0 |
| Variant | `without_smote` |
| CV F1 Score | 0.8011 ± 0.0100 |
| Holdout F1 Score | 0.8105 |

### 9.2 Dasar Pemilihan

Pemilihan berdasarkan metrik **F1 Score** karena:
1. Dataset memiliki ketidakseimbangan kelas (79.79% Terlambat vs 20.21% Tepat Waktu)
2. F1 Score merupakan harmonik mean antara Precision dan Recall
3. Model tanpa SMOTE memiliki F1 Score lebih tinggi pada CV dan Holdout

### 9.3 Lokasi Artifact

| File | Path |
|---|---|
| Model Artifact | `models/gaussian_nb_8_features/without_smote/model.joblib` |
| Metadata JSON | `models/gaussian_nb_8_features/without_smote/metadata.json` |

---

## 10. Inference

### 10.1 Data Inference

| Komponen | Nilai |
|---|---|
| Sumber | `iceberg.feature_store.inference_dataset` |
| Filter | `status_mahasiswa = 'AKTIF'` |
| Angkatan | 2022, 2023, 2024 |
| Jumlah | 12.501 mahasiswa |

### 10.2 Snapshot Data (2026)

| Angkatan | Semester Aktif | Target SKS | Keterangan |
|---|---|---|---|
| 2022 | 7 | 135 | Semester 7 pada 2026 |
| 2023 | 5 | 95 | Semester 5 pada 2026 |
| 2024 | 3 | 55 | Semester 3 pada 2026 |

### 10.3 Feature yang Digunakan

Inference menggunakan **8 fitur yang sama** dengan training:

```python
INFERENCE_FEATURES = [
    "jk_enc",
    "angkatan",
    "ip",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "sks_seharusnya",
    "selisih_sks",
]
```

### 10.4 Hasil Prediksi

#### Tanpa SMOTE (Model Terpilih)

| Hasil Prediksi | Jumlah | Persentase |
|---|---:|---:|
| Tepat Waktu (0) | 160 | 1,28% |
| Terlambat (1) | 12.341 | 98,72% |
| **Total** | **12.501** | **100%** |

#### Dengan SMOTE

| Hasil Prediksi | Jumlah | Persentase |
|---|---:|---:|
| Tepat Waktu (0) | 255 | 2,04% |
| Terlambat (1) | 12.246 | 97,96% |
| **Total** | **12.501** | **100%** |

### 10.5 Perbandingan Model (Agreement/Disagreement)

| Metrik | Nilai |
|---|---|
| Total ID dibandingkan | 12.501 |
| **Agree** | **12.406 (99,24%)** |
| **Disagree** | **95 (0,76%)** |

Pola disagreement:
- 95 kasus: model dengan SMOTE memprediksi "Tepat Waktu" (0), tetapi model tanpa SMOTE memprediksi "Terlambat" (1)

### 10.6 Distribusi Hasil Prediksi Berdasarkan Angkatan

Bagian ini menganalisis distribusi hasil inference berdasarkan angkatan mahasiswa (2022, 2023, dan 2024) untuk melihat pola prediksi kelulusan pada masing-masing tahun masuk.

**Sumber data:** File Parquet hasil inference (`prediction_result_without_smote.parquet` dan `prediction_result_with_smote.parquet`)

#### Prediksi Tanpa SMOTE

| Angkatan | Tepat Waktu | Terlambat | Total | % Tepat Waktu | % Terlambat |
|----------|-------------|-----------|-------|---------------|-------------|
| 2022 | 160 | 3.949 | 4.109 | 3,89% | 96,11% |
| 2023 | 0 | 4.046 | 4.046 | 0,00% | 100,00% |
| 2024 | 0 | 4.346 | 4.346 | 0,00% | 100,00% |
| **TOTAL** | **160** | **12.341** | **12.501** | **1,28%** | **98,72%** |

**Interpretasi:**
- Mahasiswa angkatan 2022 memiliki sedikit prediksi "Tepat Waktu" (160 dari 4.109 mahasiswa, atau 3,89%). Hal ini dikarenakan angkatan 2022 berada di semester 7 dengan target SKS 135, sehingga sebagian kecil mahasiswa sudah mencapai target tersebut.
- Mahasiswa angkatan 2023 dan 2024 semuanya diprediksi "Terlambat" (0% Tepat Waktu). Hal ini wajar karena angkatan 2023 baru di semester 5 (target 95 SKS) dan angkatan 2024 baru di semester 3 (target 55 SKS), sehingga belum mencapai target kelulusan.
- Secara keseluruhan, hanya 1,28% mahasiswa inference yang diprediksi lulus tepat waktu, yang semuanya berasal dari angkatan 2022.

#### Prediksi Dengan SMOTE

| Angkatan | Tepat Waktu | Terlambat | Total | % Tepat Waktu | % Terlambat |
|----------|-------------|-----------|-------|---------------|-------------|
| 2022 | 255 | 3.854 | 4.109 | 6,21% | 93,79% |
| 2023 | 0 | 4.046 | 4.046 | 0,00% | 100,00% |
| 2024 | 0 | 4.346 | 4.346 | 0,00% | 100,00% |
| **TOTAL** | **255** | **12.246** | **12.501** | **2,04%** | **97,96%** |

**Interpretasi:**
- Model dengan SMOTE memberikan lebih banyak prediksi "Tepat Waktu" pada angkatan 2022 (255 dari 4.109 mahasiswa, atau 6,21%), dibandingkan model tanpa SMOTE (160 mahasiswa, 3,89%).
- Sama seperti model tanpa SMOTE, model dengan SMOTE memprediksi 100% "Terlambat" untuk angkatan 2023 dan 2024.
- Peningkatan prediksi "Tepat Waktu" pada angkatan 2022 dengan SMOTE (+95 mahasiswa) menunjukkan bahwa oversampling kelas minoritas (Tepat Waktu) membuat model lebih sensitif terhadap pola mahasiswa yang berpotensi lulus tepat waktu.

#### Perbandingan Distribusi Prediksi Tanpa SMOTE dan Dengan SMOTE

| Angkatan | Tepat Waktu Tanpa SMOTE | Tepat Waktu Dengan SMOTE | Δ Tepat Waktu | Terlambat Tanpa SMOTE | Terlambat Dengan SMOTE | Δ Terlambat |
|----------|-------------------------|--------------------------|---------------|-----------------------|------------------------|-------------|
| 2022 | 160 | 255 | +95 | 3.949 | 3.854 | -95 |
| 2023 | 0 | 0 | 0 | 4.046 | 4.046 | 0 |
| 2024 | 0 | 0 | 0 | 4.346 | 4.346 | 0 |

**Interpretasi Perubahan:**

1. **Angkatan 2022:** Terjadi perubahan signifikan dengan penggunaan SMOTE. Jumlah mahasiswa yang diprediksi "Tepat Waktu" meningkat dari 160 menjadi 255 (peningkatan +95 mahasiswa atau +59,38%). Sebaliknya, prediksi "Terlambat" berkurang dari 3.949 menjadi 3.854 (pengurangan -95 mahasiswa). Hal ini menunjukkan bahwa SMOTE membantu model mengenali lebih banyak pola mahasiswa yang berpotensi lulus tepat waktu.

2. **Angkatan 2023 dan 2024:** Tidak ada perubahan prediksi antara model tanpa dan dengan SMOTE. Kedua model memprediksi 100% "Terlambat" untuk kedua angkatan ini. Hal ini konsisten karena data fitur mahasiswa angkatan 2023 dan 2024 menunjukkan bahwa mereka masih jauh dari target SKS yang harus dicapai.

3. **Pola Umum:** SMOTE hanya mempengaruhi prediksi pada angkatan 2022 yang memang memiliki beberapa mahasiswa dengan fitur yang mendekati ambang batas "Tepat Waktu". Untuk angkatan yang masih jauh dari target (2023 dan 2024), SMOTE tidak memberikan dampak pada hasil prediksi.

---

## 11. Output Inference

### 11.1 Struktur Output (Parquet)

Setiap baris prediction result berisi:

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `id_mahasiswa` | String | Identifier unik mahasiswa |
| `jk_enc` | Integer | Jenis kelamin (0/1) |
| `angkatan` | Integer | Tahun masuk |
| `ip` | Double | IP semester terakhir |
| `ipk` | Double | IPK kumulatif |
| `total_sks` | Integer | Total SKS ditempuh |
| `jumlah_mk` | Integer | Jumlah mata kuliah ditempuh |
| `sks_seharusnya` | Integer | Target SKS |
| `selisih_sks` | Integer | Selisih SKS |
| `prediksi_label` | Integer | Label prediksi (0 atau 1) |
| `prediksi` | String | Label teks ("Tepat Waktu" atau "Terlambat") |
| `probability_tepat_waktu` | Double | Probabilitas kelas 0 |
| `probability_terlambat` | Double | Probabilitas kelas 1 |
| `prediction_timestamp` | String | Timestamp prediksi |
| `model_version` | String | Versi model (v4.0.0) |
| `model_variant` | String | Varian model (without_smote/with_smote) |

### 11.2 File Output

| File | Lokasi |
|---|---|
| Prediction Result (tanpa SMOTE) | `data/predictions/prediction_result_without_smote.parquet` |
| Prediction Result (dengan SMOTE) | `data/predictions/prediction_result_with_smote.parquet` |
| Comparison | `data/predictions/prediction_comparison.parquet` |

---

## 12. Penyimpanan Hasil ML di Iceberg

### 12.1 Tabel Iceberg

Hasil ML disimpan ke tiga tabel Iceberg pada namespace `hive_iceberg.feature_store`:

| Tabel | Jumlah Baris | Status |
|---|---:|---|
| `prediction_result_without_smote` | 12.501 | ✅ SUCCESS |
| `prediction_result_with_smote` | 12.501 | ✅ SUCCESS |
| `prediction_comparison` | 12.501 | ✅ SUCCESS |

### 12.2 Validasi Iceberg Output

| Validasi | Status |
|---|---|
| Row count match | ✅ PASS |
| Unique ID | ✅ PASS |
| NULL check | ✅ PASS (0 null) |
| Schema match | ✅ PASS |
| Grain (1 baris = 1 mahasiswa) | ✅ PASS |

### 12.3 Feature Store Tables

| Tabel | Jumlah Baris | Keterangan |
|---|---:|---|
| `training_dataset` | 15.599 | Data training LULUS |
| `inference_dataset` | 12.501 | Data inference AKTIF 2022-2024 |

---

## 13. Integrasi Trino dan Superset

### 13.1 Trino

Semua tabel Iceberg dapat diakses melalui Trino:

```sql
-- Melihat semua tabel
SHOW TABLES FROM iceberg.feature_store;

-- Query prediction result
SELECT * FROM iceberg.feature_store.prediction_result_without_smoke LIMIT 10;

-- Melihat distribution prediksi
SELECT prediksi_label, COUNT(*) as jumlah
FROM iceberg.feature_store.prediction_result_without_smoke
GROUP BY prediksi_label;
```

### 13.2 Superset

Berikut dataset yang terdaftar di Superset:

| ID | Dataset | Schema | Tabel |
|---|---|---|---|
| 27 | Academic Trino | gold | dim_mahasiswa |
| 28 | Academic Trino | gold | fact_khs |
| 29 | Academic Trino | feature_store | training_dataset |
| 30 | Academic Trino | feature_store | inference_dataset |
| 31 | Academic Trino | feature_store | prediction_result_without_smote |
| 32 | Academic Trino | feature_store | prediction_result_with_smote |
| 33 | Academic Trino | feature_store | prediction_comparison |

### 13.3 Dashboard

Dashboard yang sudah ada (`Dashboard Prediksi Tingkat Kelulusan Mahasiswa`, id=3) menggunakan dataset:
- `gold.data_referensi_mahasiswa`
- `gold.model_metrics_final`
- `gold.model_predictions`
- `gold.confusion_matrix_final`
- `gold.classification_report_final`
- `gold.prediction_by_angkatan_final`

---

## 14. Alur End-to-End

```mermaid
flowchart LR
    A[Bronze] --> B[Silver]
    B --> C[Gold]
    C --> D[Feature Store]
    D --> E[ML Training]
    E --> F[Model Registry]
    D --> G[Inference]
    F --> G
    G --> H[Iceberg ML Output]
    H --> I[Trino]
    I --> J[Superset]

    style A fill:#8B4513,color:#fff
    style B fill:#C0C0C0,color:#000
    style D fill:#FFD700,color:#000
    style E fill:#9370DB,color:#fff
    style F fill:#9370DB,color:#fff
    style G fill:#9370DB,color:#fff
    style H fill:#1E90FF,color:#fff
    style I fill:#FF6347,color:#fff
    style J fill:#32CD32,color:#fff
```

### Keterangan Alur

1. **Bronze → Silver**: Data mentah diproses, dibersihkan, dan dinormalisasi
2. **Silver → Gold**: Data dikonsolidasi menjadi wide schema `dim_mahasiswa` (16 kolom)
3. **Gold → Feature Store**: Dilakukan encoding (`jk_enc`), filtering data training (LULUS) dan inference (AKTIF 2022-2024), serta snapshot 2026
4. **Feature Store → ML Training**: Model GaussianNB di-training dengan dua varian (tanpa/dengan SMOTE)
5. **ML Training → Model Registry**: Artifact model disimpan di `models/gaussian_nb_8_features/`
6. **Feature Store + Model Registry → Inference**: Model memprediksi data inference 12.501 mahasiswa aktif
7. **Inference → Iceberg ML Output**: Hasil prediksi ditulis ke tabel Iceberg
8. **Iceberg → Trino**: Tabel Iceberg dapat diquery melalui Trino
9. **Trino → Superset**: Dataset terdaftar di Superset untuk visualisasi dashboard

---

## 15. Rekonciliasi dan Root Cause Analysis

### 15.1 Masalah yang Ditemukan

Sebelum perbaikan, pipeline inference hanya menghasilkan **12.244** mahasiswa, padahal populasi aktual mahasiswa AKTIF angkatan 2022-2024 adalah **12.501** mahasiswa. Terdapat **257 mahasiswa** yang hilang.

### 15.2 Root Cause

**Root cause:** Pada `inference_dataset.py` (baris 98), terdapat perintah:

```python
valid = aktif.dropna(subset=FEATURE_X)
```

Perintah ini menghapus semua baris yang memiliki NULL pada salah satu dari 8 fitur. Masalahnya, kolom `ip` (Indeks Prestasi semester terakhir) berasal dari tabel `fact_khs` (KHS). Mahasiswa yang tidak memiliki catatan KHS akan memiliki `ip = NULL` di Gold Layer setelah LEFT JOIN.

**Distribusi 257 mahasiswa tanpa KHS:**

| Angkatan | Jumlah Hilang |
|---|---:|
| 2022 | 122 |
| 2023 | 61 |
| 2024 | 74 |
| **Total** | **257** |

### 15.3 Solusi

Untuk mempertahankan seluruh 12.501 mahasiswa inference, dilakukan imputasi:

```python
# Imputasi ip = ipk untuk mahasiswa tanpa KHS
aktif = aktif.withColumn(
    "ip",
    F.when(F.col("ip").isNull(), F.col("ipk")).otherwise(F.col("ip")),
)
```

**Alasan imputasi:**
1. Mahasiswa tanpa KHS memiliki `ipk` (GPA kumulatif) tetapi tidak memiliki `ip` (GPA semester terakhir)
2. `ipk` digunakan sebagai pendekatan yang wajar karena mencakup seluruh riwayat akademik
3. Imputasi ini hanya berlaku untuk data **inference** (bukan training)

### 15.4 Reconciliation Table

| Tahap | 2022 | 2023 | 2024 | Total |
|---|---:|---:|---:|---:|
| Gold (AKTIF) | 4.109 | 4.046 | 4.346 | **12.501** |
| Feature Store | 4.109 | 4.046 | 4.346 | **12.501** |
| ML Inference | 4.109 | 4.046 | 4.346 | **12.501** |
| Iceberg Output | 4.109 | 4.046 | 4.346 | **12.501** |

**Status:** ✅ Seluruh tahap mempertahankan 12.501 mahasiswa tanpa ada yang hilang.

### 15.5 File yang Diubah

| File | Perubahan |
|---|---|
| `backend/feature_store/inference_dataset.py` | Tambah imputasi `ip = ipk` untuk mahasiswa tanpa KHS, tambah reconciliation check |

---

## Lampiran

### A. Model Artifact Files

```
models/gaussian_nb_8_features/
├── without_smote/
│   ├── model.joblib          (GaussianNB artifact)
│   └── metadata.json         (CV + Holdout metrics)
├── with_smote/
│   ├── model.joblib          (SMOTE + GaussianNB artifact)
│   └── metadata.json         (CV + Holdout metrics)
└── (4_features/ - legacy, tidak digunakan)
```

### B. Source Code Files

| File | Fungsi |
|---|---|
| `backend/ml/data_preparation.py` | Load dataset, validasi, build X/y |
| `backend/ml/train.py` | Training pipeline, CV, holdout test |
| `backend/ml/registry.py` | Simpan/load model artifact |
| `backend/ml/inference.py` | Prediksi inference dataset |
| `backend/ml/evaluate.py` | Orkestrasi training + quality gate |
| `backend/ml/iceberg_output.py` | Tulis hasil ke Iceberg |
| `backend/feature_store/feature_engineering.py` | Encoding, leakage check |
| `backend/feature_store/training_dataset.py` | Build training dataset |
| `backend/feature_store/inference_dataset.py` | Build inference dataset |

### C. Quality Reports

| File | Deskripsi |
|---|---|
| `logs/inference_quality_report.json` | Hasil validasi inference |
| `logs/inference_iceberg_quality_report.json` | Hasil validasi Iceberg output |
| `logs/training_quality_report.json` | Hasil validasi training |

### D. Perintah Verifikasi

```bash
# Smoke test
docker compose exec -T airflow-scheduler python /opt/airflow/scripts/smoke_test_v4.py

# Verifikasi Trino
docker compose exec -T trino trino --server trino:8082 --catalog iceberg \
  --execute "SHOW TABLES FROM iceberg.feature_store"

# Cek jumlah prediksi
docker compose exec -T trino trino --server trino:8082 --catalog iceberg \
  --execute "SELECT count(*) FROM iceberg.feature_store.prediction_result_without_smote"
```

---

*Terakhir diperbarui: 2026-09-02*  
*Pipeline Version: v4.0.0*  
*Model: GaussianNB tanpa SMOTE (CV F1 = 0.8011)*  
*Inference: 12.501 mahasiswa AKTIF (2022-2024)*
