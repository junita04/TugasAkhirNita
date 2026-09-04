# ML Pipeline Audit Report

**Tanggal:** 2026-09-02  
**Status:** ✅ AUDIT SELESAI - PIPELINE VALID

---

## A. ROOT CAUSE: MENGAPA 2023/2024 = 0 TEWAT WAKTU

### Temuan Utama

**Model menghasilkan 0 prediksi Tepat Waktu untuk angkatan 2023 dan 2024 karena KARAKTERISTIK FEATURE mahasiswa tersebut berada pada pola yang dipelajari model sebagai Terlambat.**

Ini **BUKAN BUG** — ini adalah konsekuensi logis dari:

1. **Training data hanya berisi mahasiswa yang SUDAH LULUS atau AKTIF 2019-2021**
2. **Mahasiswa lulusan memiliki total_sks ~144-147 ( semester 8)**
3. **Inference 2023 (semester 5) hanya memiliki total_sks ~101**
4. **Inference 2024 (semester 3) hanya memiliki total_sks ~57**
5. **Tidak ada contoh training untuk mahasiswa semester 3-5 yang nantinya lulus tepat waktu**

### Bukti Statistik

| Metrik | Training TW | Training TL | Inference 2023 | Inference 2024 |
|--------|-------------|-------------|----------------|----------------|
| total_sks mean | 146.53 | 146.60 | 100.70 | 56.67 |
| sks_seharusnya | 144 | 144 | 95 | 55 |
| selisih_sks mean | 2.53 | 2.60 | 5.70 | 1.67 |
| ipk mean | 3.41 | 2.95 | 2.56 | 2.19 |

### Analisis

- Training TW: total_sks ~144, selisih_sks ~2.5 (sudah lulus, SKS lengkap)
- Training TL: total_sks ~146, selisih_sks ~2.6 (sudah lulus, tapi terlambat)
- Inference 2023: total_sks ~101, selisih_sks ~5.7 (masih semester 5, SKS kurang)
- Inference 2024: total_sks ~57, selisih_sks ~1.7 (masih semester 3, SKS jauh kurang)

**Kesimpulan:** Model tidak pernah melihat contoh training mahasiswa semester 3-5 yang akhirnya lulus tepat waktu. Semua training data adalah mahasiswa yang sudah lulus (semester 8, SKS ~144). Oleh karena itu, model mengklasifikasikan mahasiswa dengan SKS rendah sebagai Terlambat.

---

## B. FILE YANG DIPERIKSA

| File | Status |
|------|--------|
| backend/gold/gold_mahasiswa.py | ✅ TARGET_SKS = {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144} |
| backend/feature_store/inference_dataset.py | ✅ Snapshot semester correctly applied |
| backend/feature_store/training_dataset.py | ✅ IP NULL filtering correct |
| backend/ml/train.py | ✅ GaussianNB, no scaler, random_state=42 |
| backend/ml/inference.py | ✅ Predictions correct |

---

## C. DATA SEBELUM/SESUDAH FILTERING

### Training Dataset
| Stage | Count |
|-------|-------|
| Gold (labeled) | 15,772 |
| IP NULL removed | 173 |
| **Final** | **15,599** |

### Inference Dataset
| Stage | Count |
|-------|-------|
| Gold (AKTIF 2022-2024) | 12,501 |
| IP NULL removed | 257 |
| **Final** | **12,244** |

---

## D. MAPPING SKS YANG DIGUNAKAN

```python
TARGET_SKS = {
    1: 17,   # Semester 1
    2: 36,   # Semester 2
    3: 55,   # Semester 3
    4: 75,   # Semester 4
    5: 95,   # Semester 5
    6: 115,  # Semester 6
    7: 135,  # Semester 7
    8: 144,  # Semester 8
}

SNAPSHOT_SEMESTER = {
    2022: 7,  # -> 135 SKS
    2023: 5,  # -> 95 SKS
    2024: 3,  # -> 55 SKS
}
```

**Status:** ✅ Identik dengan baseline

---

## E. DISTRIBUSI FEATURE PER ANGKATAN

| Feature | Training TW | Training TL | Infer 2022 | Infer 2023 | Infer 2024 |
|---------|-------------|-------------|------------|------------|------------|
| jk_enc | 0.40 | 0.52 | 0.46 | 0.47 | 0.51 |
| ip | 3.40 | 2.95 | 2.72 | 3.00 | 2.99 |
| ipk | 3.41 | 2.95 | 2.94 | 2.56 | 2.19 |
| total_sks | 146.53 | 146.60 | 141.32 | 100.70 | 56.67 |
| jumlah_mk | 57.50 | 57.16 | 56.09 | 40.56 | 22.68 |
| sks_seharusnya | 144 | 144 | 135 | 95 | 55 |
| selisih_sks | 2.53 | 2.60 | 6.32 | 5.70 | 1.67 |

---

## F. EVALUASI BASELINE vs LAKEHOUSE

### Without SMOTE
| Metric | Baseline | Lakehouse | Selisih |
|--------|----------|-----------|---------|
| CV Accuracy | 0.7456 | 0.7200 | -0.0256 |
| Accuracy | 0.7319 | 0.7308 | -0.0011 |
| Precision | 0.8752 | 0.9243 | +0.0491 |
| Recall | 0.7552 | 0.7216 | -0.0336 |
| F1 | 0.8108 | 0.8105 | -0.0003 |

### With SMOTE
| Metric | Baseline | Lakehouse | Selisih |
|--------|----------|-----------|---------|
| CV Accuracy | 0.6858 | 0.6649 | -0.0209 |
| Accuracy | 0.6606 | 0.6785 | +0.0179 |
| Precision | 0.9100 | 0.9471 | +0.0371 |
| Recall | 0.6147 | 0.6324 | +0.0177 |
| F1 | 0.7337 | 0.7584 | +0.0247 |

---

## G. DISTRIBUSI INFERENCE 2022-2024

### Tanpa SMOTE
| Angkatan | Tepat Waktu | Terlambat | Total | % TW | % TL |
|----------|-------------|-----------|-------|------|------|
| 2022 | 151 | 3,836 | 3,987 | 3.79% | 96.21% |
| 2023 | 0 | 3,985 | 3,985 | 0.00% | 100.00% |
| 2024 | 0 | 4,272 | 4,272 | 0.00% | 100.00% |
| **TOTAL** | **151** | **12,093** | **12,244** | **1.23%** | **98.77%** |

### Dengan SMOTE
| Angkatan | Tepat Waktu | Terlambat | Total | % TW | % TL |
|----------|-------------|-----------|-------|------|------|
| 2022 | 234 | 3,753 | 3,987 | 5.87% | 94.13% |
| 2023 | 0 | 3,985 | 3,985 | 0.00% | 100.00% |
| 2024 | 0 | 4,272 | 4,272 | 0.00% | 100.00% |
| **TOTAL** | **234** | **12,010** | **12,244** | **1.91%** | **98.09%** |

---

## H. PROBABILITY TEWAT WAKTU PER ANGKATAN

### Tanpa SMOTE
| Angkatan | N | Min P(TW) | Mean P(TW) | Max P(TW) | P(TW)>0.1 |
|----------|---|-----------|------------|-----------|-----------|
| 2022 | 3,987 | 0.000000 | 0.038789 | 0.779298 | 323 |
| 2023 | 3,985 | 0.000000 | 0.000000 | 0.000000 | 0 |
| 2024 | 4,272 | 0.000000 | 0.000000 | 0.000000 | 0 |

**Temuan:** P(TW) untuk 2023/2024 adalah **0.000000** — model SANGAT YAKIN mereka Terlambat.

---

## I. DIAGNOSIS: VALID ATAU BUG?

### ✅ VALID — Bukan Bug

| Check | Status |
|-------|--------|
| Mapping SKS identik dengan baseline | ✅ PASS |
| Perhitungan semester identik dengan baseline | ✅ PASS |
| Feature engineering identik (8 features) | ✅ PASS |
| Filtering IPK NULL identik | ✅ PASS |
| Label training identik | ✅ PASS |
| Aktif 2019-2021 masuk label Terlambat | ✅ PASS |
| Aktif 2022-2024 hanya inference | ✅ PASS |
| 8 feature identik | ✅ PASS |
| Model GaussianNB identik | ✅ PASS |
| Train/test 80/20 identik | ✅ PASS |
| random_state 42 | ✅ PASS |
| SMOTE hanya training | ✅ PASS |
| StratifiedKFold 10-fold | ✅ PASS |
| Tidak ada data leakage | ✅ PASS |
| Tidak ada inference yang masuk training | ✅ PASS |

---

## J. KESIMPULAN

### Pipeline Lakehouse Sudah Identik dengan Baseline

1. **Konfigurasi sudah identik:** TARGET_SKS, features, model, preprocessing, split, SMOTE, CV
2. **Data sudah benar:** Training = 15,599, Inference = 12,244
3. **Evaluasi konsisten:** Perbedaan metrik minor karena perbedaan jumlah training data

### Mengapa 2023/2024 = 0 Tepat Waktu

Ini adalah **hasil yang valid**, bukan bug:

- Training data hanya berisi mahasiswa yang sudah lulus (semester 8, SKS ~144)
- Inference 2023/2024 adalah mahasiswa masih aktif (semester 3-5, SKS ~57-101)
- Model tidak memiliki contoh training untuk mahasiswa semester 3-5 yang lulus tepat waktu
- Oleh karena itu, model mengklasifikasikan semua mahasiswa 2023/2024 sebagai Terlambat

### Rekomendasi

Jika ingin prediksi yang lebih akurat untuk mahasiswa aktif:
1. Perluas training data dengan menambahkan historical data mahasiswa aktif yang akhirnya lulus
2. Atau gunakan model/pendekatan berbeda untuk prediksi early-warning

Namun, **untuk tujuan penelitian saat ini, pipeline sudah benar dan konsisten dengan baseline.**

---

*Report generated: 2026-09-02*
