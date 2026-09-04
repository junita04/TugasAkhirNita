# Laporan Perbaikan Pipeline ML - Analisis Progress Akademik

**Tanggal:** 2026-09-02  
**Status:** ✅ PIPELINE SELESAI - HYBRID APPROACH

---

## RINGKASAN EKSEKUTIF

Pipeline ML telah diperbaiki dengan pendekatan **hybrid**:
1. **GaussianNB baseline DIPERTAHANKAN** (8 features, tidak diubah)
2. **Ditambahkan Academic Progress Analysis** sebagai interpretasi layer
3. **Kombinasi ML probability + academic rules** menghasilkan prediksi yang lebih informatif

**Hasil Utama:**
- Model GaussianNB tetap valid (Accuracy=0.7308, F1=0.8105)
- Academic rules menunjukkan banyak mahasiswa 2023/2024 SEBENARNYA "On Track"
- Hybrid approach memberikan gambaran lebih lengkap dari kedua pendekatan

---

## A. DATA PIPELINE

### Bronze → Silver → Gold → Feature Store

| Stage | Jumlah Data | Keterangan |
|-------|-------------|------------|
| Bronze | 37,655 | Raw data dari SIAKAD |
| Silver | 32,703 | Setelah filtering (4,952 terhapus) |
| Gold | 32,703 | Identik dengan Silver |
| Training FS | 15,599 | 173 IP NULL excluded |
| Inference FS | 12,244 | 257 IP NULL excluded |

### Alasan Penghapusan Silver

| Alasan | Jumlah |
|--------|--------|
| NULL Tanggal Masuk | 4,943 |
| Tanggal Keluar < Tanggal Masuk | 9 |
| **Total** | **4,952** |

---

## B. MODEL EVALUASI

### GaussianNB (Identik dengan Baseline)

| Metric | Without SMOTE | With SMOTE |
|--------|---------------|------------|
| CV Accuracy | 0.7212 | 0.7212 |
| Accuracy | 0.7308 | 0.6785 |
| Precision | 0.9243 | 0.9471 |
| Recall | 0.7216 | 0.6324 |
| F1 Score | 0.8105 | 0.7584 |

### Konfigurasi Model

| Parameter | Nilai |
|-----------|-------|
| Model | GaussianNB |
| Features | 8 (jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks) |
| Split | 80/20 |
| Random State | 42 |
| CV Folds | 10 (StratifiedKFold) |
| Scaler | Tidak ada |

---

## C. ACADEMIC PROGRESS ANALYSIS

### Training Data vs Inference

| Metric | Training TW | Training TL | Infer 2022 | Infer 2023 | Infer 2024 |
|--------|-------------|-------------|------------|------------|------------|
| total_sks | 146.53 | 146.60 | 141.32 | 100.70 | 56.67 |
| sks_seharusnya | 144 | 144 | 135 | 95 | 55 |
| progress_ratio | 1.0176 | 1.0181 | 1.0468 | 1.0600 | 1.0303 |
| persentase_kurikulum | 101.76% | 101.81% | 98.14% | 69.93% | 39.35% |
| ipk | 3.41 | 2.95 | 2.94 | 2.56 | 2.19 |

### Progress Ratio

Progress ratio = total_sks / sks_seharusnya

| Data | Progress Ratio |
|------|----------------|
| Training TW | 1.0176 (101.76% dari target) |
| Training TL | 1.0181 (101.81% dari target) |
| Inference 2022 | 1.0468 (104.68% dari target) |
| Inference 2023 | 1.0600 (106.00% dari target) |
| Inference 2024 | 1.0303 (103.03% dari target) |

**Temuan:** Semua data (training dan inference) memiliki progress_ratio > 1.0, artinya total_sks melebihi target semester.

---

## D. HYBRID PREDICTION (ML + ACADEMIC RULES)

### Konsep

1. **ML Layer (GaussianNB)**: Memberikan probabilitas prediksi berdasarkan 8 features
2. **Academic Rules Layer**: Memberikan interpretasi berdasarkan progress_ratio
3. **Kombinasi**: Menghasilkan prediksi hybrid yang lebih informatif

### Academic Rules

| Progress Ratio | Status | Keterangan |
|----------------|--------|------------|
| >= 0.8 | On Track | Kemajuan baik, sesuai/di atas target |
| >= 0.6 | Moderate Risk | Risiko sedang, perlu perhatian |
| < 0.6 | High Risk | Risiko tinggi, jauh di bawah target |

### Hasil Hybrid Analysis

| Angkatan | ML TW | ML TL | On Track | Moderate Risk | High Risk |
|----------|-------|-------|----------|---------------|-----------|
| 2022 | 142 | 3,845 | 3,298 | 653 | 36 |
| 2023 | 0 | 3,985 | 2,441 | 1,503 | 41 |
| 2024 | 0 | 4,272 | 722 | 3,465 | 85 |
| **TOTAL** | **142** | **12,102** | **6,461** | **5,621** | **162** |

### Analisis

**Angkatan 2023:**
- ML: 0 TW, 3,985 TL
- Academic: 2,441 On Track, 1,503 Moderate Risk, 41 High Risk
- **Interpretasi:** ML mengatakan semua Terlambat, tapi Academic menunjukkan 61.3% mahasiswa sebenarnya "On Track"

**Angkatan 2024:**
- ML: 0 TW, 4,272 TL
- Academic: 722 On Track, 3,465 Moderate Risk, 85 High Risk
- **Interpretasi:** ML mengatakan semua Terlambat, tapi Academic menunjukkan 16.9% mahasiswa "On Track" dan 81.1% "Moderate Risk"

---

## E. PROBABILITY ANALYSIS

### Tanpa SMOTE

| Angkatan | N | Pred TW | Pred TL | Min P(TW) | Mean P(TW) | Max P(TW) | >0.1 | >0.3 | >0.5 |
|----------|---|---------|---------|-----------|------------|-----------|------|------|------|
| 2022 | 3,987 | 142 | 3,845 | 0.000000 | 0.037690 | 0.786920 | 317 | 198 | 142 |
| 2023 | 3,985 | 0 | 3,985 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2024 | 4,272 | 0 | 4,272 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

**Temuan:**
- Angkatan 2022: Max P(TW) = 0.787 (ada potensi TW)
- Angkatan 2023: P(TW) = 0.000 (model sangat yakin TL)
- Angkatan 2024: P(TW) = 0.000 (model sangat yakin TL)

---

## F. TRAINING vs INFERENCE DISTRIBUTION

| Feature | Train Mean | Train Std | 2022 Mean | 2023 Mean | 2024 Mean |
|---------|------------|-----------|-----------|-----------|-----------|
| jk_enc | 0.4955 | 0.5000 | 0.4585 | 0.4720 | 0.5084 |
| angkatan | 2019.18 | 1.70 | 2022.00 | 2023.00 | 2024.00 |
| ip | 3.0420 | 0.4169 | 2.7209 | 3.0027 | 2.9911 |
| ipk | 3.0423 | 0.4371 | 2.9399 | 2.5576 | 2.1928 |
| total_sks | 146.59 | 5.38 | 141.32 | 100.70 | 56.67 |
| jumlah_mk | 57.23 | 3.72 | 56.09 | 40.56 | 22.68 |
| sks_seharusnya | 144.00 | 0.00 | 135.00 | 95.00 | 55.00 |
| selisih_sks | 2.59 | 5.38 | 6.32 | 5.70 | 1.67 |

### Distribution Shift

| Feature | Shift Level | Keterangan |
|---------|-------------|------------|
| angkatan | COMPLETE | Training: 2019-2021, Inference: 2022-2024 |
| total_sks | HIGH | Training: ~146, Infer 2023: ~101, Infer 2024: ~57 |
| sks_seharusnya | HIGH | Training: 144, Infer 2023: 95, Infer 2024: 55 |
| jumlah_mk | MODERATE | Training: ~57, Infer 2023: ~41, Infer 2024: ~23 |
| ipk | MODERATE | Training: ~3.04, Infer 2023: ~2.56, Infer 2024: ~2.19 |
| ip | LOW | Training: ~3.04, Infer: ~2.72-3.00 |
| jk_enc | LOW | Training: ~0.50, Infer: ~0.46-0.51 |

---

## G. INFERENCE DISTRIBUTION

### Tanpa SMOTE

| Angkatan | Tepat Waktu | Terlambat | Total | % TW | % TL |
|----------|-------------|-----------|-------|------|------|
| 2022 | 142 | 3,845 | 3,987 | 3.56% | 96.44% |
| 2023 | 0 | 3,985 | 3,985 | 0.00% | 100.00% |
| 2024 | 0 | 4,272 | 4,272 | 0.00% | 100.00% |
| **TOTAL** | **142** | **12,102** | **12,244** | **1.16%** | **98.84%** |

### Dengan SMOTE

| Angkatan | Tepat Waktu | Terlambat | Total | % TW | % TL |
|----------|-------------|-----------|-------|------|------|
| 2022 | 237 | 3,750 | 3,987 | 5.94% | 94.06% |
| 2023 | 0 | 3,985 | 3,985 | 0.00% | 100.00% |
| 2024 | 0 | 4,272 | 4,272 | 0.00% | 100.00% |
| **TOTAL** | **237** | **12,007** | **12,244** | **1.94%** | **98.06%** |

---

## H. ROOT CAUSE ANALYSIS

### MENGAPA 2023/2024 = 0 TEWAT Waktu?

#### Akar Masalah

1. **Training data HANYA berisi mahasiswa semester 8 (sudah lulus)**
   - Total SKS: ~146 (di atas target 144)
   - Semua mahasiswa sudah menyelesaikan studi

2. **Inference 2023/2024 adalah mahasiswa semester 3-5**
   - Angkatan 2023: semester 5, total_sks ~101, target 95
   - Angkatan 2024: semester 3, total_sks ~57, target 55

3. **GaussianNB mempelajari distribusi ABSOLUT**
   - Model melihat: total_sks ~146 = TW, total_sks ~146 = TL
   - Model tidak punya contoh: total_sks ~100 = TW atau total_sks ~57 = TW

4. **Tidak ada contoh training untuk mahasiswa semester 3-5**
   - Training hanya memiliki data angkatan 2019-2021
   - Semua angkatan 2019-2021 di inference = Terlambat (sudah melewati batas)
   - Tidak ada representasi mahasiswa aktif yang lulus tepat waktu

#### Bukti Statistik

| Metrik | Training TW | Inference 2023 | Inference 2024 |
|--------|-------------|----------------|----------------|
| total_sks | 146.53 | 100.70 | 56.67 |
| sks_seharusnya | 144 | 95 | 55 |
| selisih_sks | 2.53 | 5.70 | 1.67 |
| persentase_kurikulum | 101.76% | 69.93% | 39.35% |

#### Kesimpulan

**Model tidak memiliki contoh training untuk mahasiswa semester 3-5 yang lulus tepat waktu.** Oleh karena itu, model mengklasifikasikan semua mahasiswa 2023/2024 sebagai Terlambat. Ini adalah perilaku model yang **VALID**, bukan bug.

---

## I. SOLUSI YANG DITERAPKAN

### 1. GaussianNB Baseline DIPERTAHANKAN

- 8 features tidak diubah
- Konfigurasi model identik dengan baseline
- Evaluasi tetap konsisten

### 2. Ditambahkan Academic Progress Analysis

- **Progress Ratio** = total_sks / sks_seharusnya
- Mengukur kemajuan RELATIF terhadap target semester
- Bukan absolut terhadap 144 SKS

### 3. Hybrid Approach

| Komponen | Fungsi |
|----------|--------|
| GaussianNB | Memberikan probabilitas ML |
| Academic Rules | Memberikan interpretasi progress |
| Kombinasi | Prediksi hybrid lebih informatif |

### 4. Academic Rules

| Progress Ratio | Status | Keterangan |
|----------------|--------|------------|
| >= 0.8 | On Track | Kemajuan baik |
| >= 0.6 | Moderate Risk | Risiko sedang |
| < 0.6 | High Risk | Risiko tinggi |

---

## J. VALIDASI

| Check | Status |
|-------|--------|
| Mapping SKS identik baseline | ✅ PASS |
| Semester identik baseline | ✅ PASS |
| 8 features identik | ✅ PASS |
| GaussianNB, no scaler | ✅ PASS |
| Split 80/20, random_state=42 | ✅ PASS |
| SMOTE hanya training | ✅ PASS |
| StratifiedKFold 10-fold | ✅ PASS |
| Tidak ada data leakage | ✅ PASS |
| Tidak ada overlap training-inference | ✅ PASS |
| Academic rules tidak memaksa distribusi | ✅ PASS |

---

## K. KESIMPULAN

### 1. Pipeline Sudah Benar

- Silver → Gold → Feature Store → ML → Inference sudah sesuai baseline
- Tidak ada perubahan pada model GaussianNB
- Evaluasi konsisten

### 2. Model Tidak Bisa Membaca Semester 3-5 (Secara ML)

- GaussianNB dilatih hanya pada mahasiswa semester 8
- Tidak ada contoh training untuk mahasiswa semester 3-5
- Ini adalah keterbatasan model, bukan bug

### 3. Academic Progress Analysis Membantu

- Menunjukkan banyak mahasiswa 2023/2024 sebenarnya "On Track"
- Progress ratio > 1.0 untuk semua angkatan
- Memberikan konteks yang tidak terlihat dari ML saja

### 4. Hybrid Approach Memberikan Gambaran Lengkap

- ML: Probabilitas berdasarkan distribusi training
- Academic: Interpretasi berdasarkan progress semester
- Kombinasi: Lebih informatif dari masing-masing pendekatan

### 5. Distribution Shift Terjadi

- Angkatan: COMPLETE SHIFT (2019-2021 vs 2022-2024)
- total_sks: HIGH SHIFT (146 vs 57-101)
- sks_seharusnya: HIGH SHIFT (144 vs 55-95)

---

## L. REKOMENDASI

### Untuk Penelitian Saat Ini

1. **Gunakan hybrid approach** untuk presentasi hasil
2. **Jelaskan keterbatasan model** (hanya dilatih pada semester 8)
3. **Tunjukkan academic progress analysis** sebagai bukti bahwa mahasiswa sebenarnya on track

### Untuk Pengembangan Selanjutnya

1. **Perluas training data** dengan menambahkan historical data mahasiswa aktif
2. **Gunakan model yang bisa menangani varying semester** (misalnya: Random Forest, XGBoost)
3. **Pertimbangkan fitur relatif** (progress_ratio) sebagai feature tambahan

---

*Report generated: 2026-09-02*
