# Pipeline Re-Run Results - New Excel File

**Tanggal:** 2026-09-02  
**Source:** `(asli)req_data_rut (baruu).xlsx`  
**Status:** ✅ ALL CHECKS PASS

---

## Pipeline Summary

| Stage | Rows | Keterangan |
|-------|------|------------|
| Bronze (data_referensi_mahasiswa) | 37,655 | Raw from Excel |
| Bronze (data_khs) | 28,273 | Raw from Excel |
| Silver (silver_mahasiswa) | 32,703 | -4,952 (NULL tanggal_masuk + invalid) |
| Silver (silver_khs) | 27,843 | -430 (NULL IP + invalid) |
| Gold (fact_khs) | 27,843 | Aggregated KHS |
| Gold (dim_mahasiswa) | 32,703 | Wide schema |
| Feature Store (Training) | 15,599 | -173 IP NULL |
| Feature Store (Inference) | 12,244 | -257 IP NULL |

---

## 8 Features

```python
FEATURE_X = [
    "jk_enc",        # 0=Perempuan, 1=Laki-laki
    "angkatan",      # Tahun masuk
    "ip",            # IP dari KHS
    "ipk",           # IPK dari referensi
    "total_sks",     # Total SKS
    "jumlah_mk",     # Jumlah mata kuliah
    "sks_seharusnya", # Target SKS per semester (ITERA mapping)
    "selisih_sks",   # total_sks - sks_seharusnya
]
```

---

## Model Evaluation

### Best Model: GaussianNB - Without SMOTE

| Metric | CV (10-fold) | Test |
|--------|--------------|------|
| Accuracy | 0.7197 | 0.7295 |
| F1 Score | 0.8005 | 0.8091 |

### Comparison

| Model | CV Accuracy | CV F1 | Test Accuracy | Test F1 |
|-------|-------------|-------|---------------|---------|
| Without SMOTE | 0.7197 | **0.8005** | 0.7295 | **0.8091** |
| With SMOTE | 0.6636 | 0.7437 | 0.6779 | 0.7572 |

---

## Inference Distribution

### Per Angkatan

| Angkatan | TW | TL | Total | % TW | % TL |
|----------|----|----|-------|------|------|
| 2022 | 163 | 3,824 | 3,987 | 4.09% | 95.91% |
| 2023 | 0 | 3,985 | 3,985 | 0.00% | 100.00% |
| 2024 | 0 | 4,272 | 4,272 | 0.00% | 100.00% |
| **TOTAL** | **163** | **12,081** | **12,244** | **1.33%** | **98.67%** |

### Per Semester

| Semester | TW | TL | Total | % TW | % TL |
|----------|----|----|-------|------|------|
| 3 (2024) | 0 | 4,272 | 4,272 | 0.00% | 100.00% |
| 5 (2023) | 0 | 3,985 | 3,985 | 0.00% | 100.00% |
| 7 (2022) | 163 | 3,824 | 3,987 | 4.09% | 95.91% |

---

## Probability Analysis

| Angkatan | Min P(TW) | Max P(TW) | Mean P(TW) | >0.1 | >0.3 | >0.5 |
|----------|-----------|-----------|------------|------|------|------|
| 2022 | 0.000000 | 0.803378 | 0.041514 | 335 | 206 | 163 |
| 2023 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 0 |
| 2024 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 0 |

---

## Training vs Inference Distribution

| Feature | Train Mean | 2022 Mean | 2023 Mean | 2024 Mean |
|---------|------------|-----------|-----------|-----------|
| jk_enc | 0.4955 | 0.4585 | 0.4720 | 0.5084 |
| angkatan | 2019.18 | 2022.00 | 2023.00 | 2024.00 |
| ip | 3.0420 | 2.7209 | 3.0027 | 2.9911 |
| ipk | 3.0423 | 2.9399 | 2.5576 | 2.1928 |
| total_sks | 146.56 | 141.32 | 100.70 | 56.67 |
| jumlah_mk | 57.22 | 56.09 | 40.56 | 22.68 |
| sks_seharusnya | 144.00 | 135.00 | 95.00 | 55.00 |
| selisih_sks | 2.56 | 6.32 | 5.70 | 1.67 |

---

## Final Audit

| Check | Status |
|-------|--------|
| File Excel baru digunakan | ✅ PASS |
| Bronze berhasil | ✅ PASS |
| Silver berhasil | ✅ PASS |
| Gold berhasil | ✅ PASS |
| Feature Store berhasil | ✅ PASS |
| Tepat 8 features | ✅ PASS |
| Tidak ada StandardScaler | ✅ PASS |
| GaussianNB | ✅ PASS |
| Split 80/20 | ✅ PASS |
| random_state=42 | ✅ PASS |
| StratifiedKFold 10-fold | ✅ PASS |
| SMOTE hanya training | ✅ PASS |
| Tidak ada data leakage | ✅ PASS |
| Tidak ada imputasi IP=IPK | ✅ PASS |
| Inference hanya AKTIF 2022-2024 | ✅ PASS |
| Mapping SKS baseline digunakan | ✅ PASS |
| Rekonsiliasi data berhasil | ✅ PASS |
| Distribusi inference per angkatan tersedia | ✅ PASS |
| Evaluasi tersedia | ✅ PASS |

---

## Output Files

| File | Location |
|------|----------|
| Training data | `data/training_8_features_new.xlsx` |
| Inference data | `data/inference_2022_2024_new.xlsx` |
| Model (without SMOTE) | `models/gaussian_nb_8_features/without_smote/model.joblib` |
| Model (with SMOTE) | `models/gaussian_nb_8_features/with_smote/model.joblib` |
| Predictions | `results/prediksi_angkatan_2022_2024_new.parquet` |
| Metadata | `models/gaussian_nb_8_features/*/metadata.json` |

---

*Report generated: 2026-09-02*
