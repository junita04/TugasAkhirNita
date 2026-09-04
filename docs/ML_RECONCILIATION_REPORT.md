# ML Reconciliation Report

**Tanggal:** 2026-09-02  
**Status:** ✅ PIPELINE REBUILD SELESAI  
**TARGET_SKS:** {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}

---

## 1. RINGKASAN PIPELINE

| Tahap | Status | Keterangan |
|-------|--------|------------|
| Bronze | ✅ | 37,655 mahasiswa |
| Silver | ✅ | 32,703 mahasiswa (4,952 removed) |
| Gold | ✅ | 32,703 mahasiswa (dari Silver) |
| Feature Store Training | ✅ | 15,599 rows (173 IP NULL dikeluarkan) |
| Feature Store Inference | ✅ | 12,244 rows (257 IP NULL dikeluarkan) |
| Model Without SMOTE | ✅ | GaussianNB, CV Accuracy=0.7200 |
| Model With SMOTE | ✅ | GaussianNB, CV Accuracy=0.6649 |
| Inference | ✅ | 12,244 predictions |

---

## 2. DATA COUNT AUDIT

### 2.1 Bronze → Silver Reconciliation

| Metric | Value |
|--------|-------|
| Bronze mahasiswa | 37,655 |
| Silver mahasiswa | 32,703 |
| **Selisih** | **4,952** |

**Penyebab selisih:**
- Tanggal Masuk NULL: 4,943 mahasiswa
- Tanggal Keluar < Tanggal Masuk: 9 mahasiswa (data tidak valid)
- **Total excluded: 4,952**

### 2.2 Silver → Gold Reconciliation

| Metric | Value |
|--------|-------|
| Silver mahasiswa | 32,703 |
| Gold dim_mahasiswa | 32,703 |
| **Selisih** | **0** |

### 2.3 Gold → Feature Store Reconciliation

| Metric | Training | Inference |
|--------|----------|-----------|
| Gold (labeled/aktif) | 15,772 | 12,501 |
| IP NULL dikeluarkan | 173 | 257 |
| **Final** | **15,599** | **12,244** |

---

## 3. TARGET_SKS (DARI BASELINE)

```python
TARGET_SKS = {
    1: 17,
    2: 36,
    3: 55,
    4: 75,
    5: 95,
    6: 115,
    7: 135,
    8: 144,
}
```

**Snapshot Inference 2026:**
| Angkatan | Semester | sks_seharusnya |
|----------|----------|----------------|
| 2022 | 7 | 135 |
| 2023 | 5 | 95 |
| 2024 | 3 | 55 |

---

## 4. FITUR MODEL (8 FEATURES)

| No | Feature | Deskripsi |
|----|---------|-----------|
| 1 | jk_enc | Jenis kelamin (P=0, L=1) |
| 2 | angkatan | Tahun masuk |
| 3 | ip | Indeks Prestasi semester |
| 4 | ipk | Indeks Prestasi Kumulatif |
| 5 | total_sks | Total SKS yang ditempuh |
| 6 | jumlah_mk | Jumlah mata kuliah |
| 7 | sks_seharusnya | SKS target berdasarkan semester |
| 8 | selisih_sks | total_sks - sks_seharusnya |

---

## 5. MODEL EVALUATION

### Without SMOTE
| Metric | CV (10-fold) | Holdout (20%) |
|--------|-------------|---------------|
| Accuracy | 0.7200 ± 0.0122 | 0.7308 |
| Precision | 0.9241 ± 0.0057 | 0.9243 |
| Recall | 0.7071 ± 0.0141 | 0.7216 |
| F1 | 0.8011 ± 0.0100 | 0.8105 |

### With SMOTE
| Metric | CV (10-fold) | Holdout (20%) |
|--------|-------------|---------------|
| Accuracy | 0.6649 ± 0.0123 | 0.6785 |
| Precision | 0.9455 ± 0.0073 | 0.9471 |
| Recall | 0.6154 ± 0.0138 | 0.6324 |
| F1 | 0.7455 ± 0.0112 | 0.7584 |

---

## 6. INFERENCE DISTRIBUTION PER ANGKATAN

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

## 7. PERBANDINGAN DENGAN BASELINE

| Komponen | Baseline | Lakehouse | Status |
|----------|----------|-----------|--------|
| TARGET_SKS | {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144} | {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144} | ✅ PASS |
| Snapshot | {2022:7, 2023:5, 2024:3} | {2022:7, 2023:5, 2024:3} | ✅ PASS |
| Features | 8 features | 8 features | ✅ PASS |
| Model | GaussianNB | GaussianNB | ✅ PASS |
| Preprocessing | No scaler | No scaler | ✅ PASS |
| Train/Test | 80:20, random_state=42 | 80:20, random_state=42 | ✅ PASS |
| CV | StratifiedKFold(10) | StratifiedKFold(10) | ✅ PASS |
| Training data | 13,181 | 15,599 | ⚠️ Diff +2,418 |
| Inference data | 12,244 | 12,244 | ✅ PASS |

### Penjelasan Perbedaan Training Data

Training Lakehouse (15,599) > Baseline (13,181) karena:
- Lakehouse menyertakan 2,418 mahasiswa AKTIF 2019-2021 yang sudah melewati batas 4 tahun
- Baseline dibuat ketika mahasiswa tersebut belum melewati batas waktu

---

## 8. VALIDASI END-TO-END

| Check | Status |
|-------|--------|
| Bronze = 37,655 | ✅ PASS |
| Silver = 32,703 | ✅ PASS |
| Gold = 32,703 | ✅ PASS |
| Bronze → Silver diff = 4,952 | ✅ PASS (4,943 null tanggal + 9 invalid) |
| Silver → Gold diff = 0 | ✅ PASS |
| AKTIF 2019-2021 → Training | ✅ PASS |
| AKTIF 2022-2024 → Inference | ✅ PASS |
| IP NULL excluded from model | ✅ PASS |
| TARGET_SKS matches baseline | ✅ PASS |
| 8 features matches baseline | ✅ PASS |
| No StandardScaler | ✅ PASS |
| GaussianNB | ✅ PASS |
| Split 80:20, random_state=42 | ✅ PASS |
| StratifiedKFold(10) | ✅ PASS |
| Distribution per angkatan | ✅ PASS |
| TW + TL = Total | ✅ PASS |

---

*Report generated: 2026-09-02*
*Pipeline Version: v4.0.0*
