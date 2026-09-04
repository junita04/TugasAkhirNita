# Audit Sumber Data Terakhir

**Tanggal Audit**: 2026-09-04  
**Tujuan**: Menentukan file data asli mana yang benar-benar menjadi sumber data untuk hasil sistem yang sekarang.

---

## 1. Data Source yang Ditemukan

### File Excel Kandidat Sumber Data

| No | File | Path | Size | Tanggal Modifikasi | Kolom Referensi | Total SKS Sum |
|----|------|------|------|-------------------|-----------------|---------------|
| 1 | `(asli)req_data_rut.xlsx` | `Data/` | 1,904 KB | 12 Agu 2026 | `ID` | 3,843,516 |
| 2 | `(asli)req_data_rut (1).xlsx` | `Data/` | 2,237 KB | 27 Agu 2026 | `ID_MHS` | 3,843,516 |
| 3 | `(asli)req_data_rut (baru).xlsx` | `Data/` | 2,215 KB | 27 Agu 2026 | `ID_MHS` | 3,843,516 |
| 4 | `(asli)req_data_rut (baruu).xlsx` | `Data/` | 2,238 KB | 2 Sep 2026 | `ID_MHS` | **3,843,025** |
| 5 | `(asli)req_data_rut (baruuu).xlsx` | `Data/` | 2,245 KB | 2 Sep 2026 | `ID_MHS` | **3,841,461** |

### Perbedaan Kolom Antara File

| Fitur | `(asli)req_data_rut.xlsx` | Semua Versi Lainnya |
|-------|--------------------------|---------------------|
| Kolom ID Referensi | `ID` | `ID_MHS` |
| Format ID | `MHS64`, `MHS77` | `MHS000001`, `MHS000002` |
| Kolom KHS | `ID, IP, SKS` (3 kolom) | `ID_KHS, ID_MHS, IP, SKS` (4 kolom) |
| Jumlah AKTIF | 19,803 | 19,822 |
| Jumlah Lulus | 13,347 | 13,328 |

### Kesimpulan Perbandingan File

- **File (1), baru, baruu, baruuu** memiliki struktur kolom yang sama (`ID_MHS`, 4 kolom KHS)
- **File original** berbeda format (`ID` bukan `ID_MHS`, 3 kolom KHS)
- **File baru** dan **(1)** memiliki Total SKS sum yang sama (3,843,516)
- **File baruu** dan **baruuu** memiliki Total SKS sum yang **BERBEDA** (3,843,025 dan 3,841,461)
- Status distribusi antara (1)/baru/baruu/baruuu identik: AKTIF=19,822, Lulus=13,328

---

## 2. Trace Kode Bronze

### Entry Point yang Tersedia

| Entry Point | File yang Digunakan | Lokasi Kode |
|-------------|---------------------|-------------|
| **Airflow DAG (Production)** | `(asli)req_data_rut (1).xlsx` | `docker/airflow/dags/prediction_pipeline.py:33` |
| **pipeline_entry.py (Default)** | `(asli)req_data_rut (1).xlsx` | `backend/services/pipeline_entry.py:16` |
| **step1_bronze.py** | `req_data_rut_baru.xlsx` | `scripts/step1_bronze.py:8` |
| **load_bronze_v2.py** | `req_data_rut_baruu.xlsx` | `scripts/load_bronze_v2.py:11` |
| **full_rerun.py** | `req_data_rut_baruu.xlsx` | `scripts/full_rerun.py:19` |

### Bukti Kode

**`scripts/step1_bronze.py` baris 8:**
```python
EXCEL = Path('/opt/airflow/data/req_data_rut_baru.xlsx')
```

**`scripts/full_pipeline_final.py` baris 19:**
```python
# STEP 1: BRONZE (already loaded via step1_bronze.py)
```

**`docker/airflow/dags/prediction_pipeline.py` baris 33:**
```python
FILE_NAME = "(asli)req_data_rut (1).xlsx"
```

**`backend/services/pipeline_entry.py` baris 16:**
```python
DEFAULT_FILENAME = "(asli)req_data_rut (1).xlsx"
```

---

## 3. Pipeline Terakhir yang Dijalankan

Berdasarkan riwayat sesi, pipeline terakhir dijalankan melalui:

1. **Bronze**: `step1_bronze.py` - membaca `req_data_rut_baru.xlsx`
2. **Silver → Gold → Feature Store → ML → Inference**: `full_pipeline_final.py` - membaca dari Iceberg tables (hasil Bronze)

**Bukti dari output pipeline:**
```
STEP 1: BRONZE AUDIT
  data_referensi_mahasiswa: 37655
  data_khs: 28273
```

**Bukti file yang di-copy ke container:**
```
docker cp "(asli)req_data_rut (baru).xlsx" ...:/opt/airflow/data/req_data_rut_baru.xlsx
```

---

## 4. Trace Bronze → Silver

| Tahap | Tabel | Jumlah Baris |
|-------|-------|-------------|
| Bronze | `data_referensi_mahasiswa` | 37,655 |
| Bronze | `data_khs` | 28,273 |
| Silver | `silver_mahasiswa` | **32,703** |
| Silver | `silver_khs` | **27,843** |

**Penyebab pengurangan Silver mahasiswa (37,655 → 32,703):**
- 4,943 baris dihapus karena `tanggal_masuk` NULL
- 9 baris dihapus karena `tanggal_keluar` < `tanggal_masuk`
- Total: 4,952 baris dihapus

**Silver KHS (28,273 → 27,843):**
- 430 baris dihapus karena filter NULL/out-of-range

---

## 5. Trace Silver → Gold

| Tahap | Tabel | Jumlah Baris |
|-------|-------|-------------|
| Silver | `silver_mahasiswa` | 32,703 |
| Silver | `silver_khs` | 27,843 |
| Gold | `fact_khs` (agregasi KHS per mahasiswa) | **27,843** |
| Gold | `dim_mahasiswa` (LEFT JOIN silver + fact) | **32,703** |

**Gold dim_mahasiswa dibuat dari:**
- `silver_mahasiswa` (32,703 baris) LEFT JOIN `fact_khs` (27,843 baris)
- Grain: 1 baris = 1 mahasiswa
- Kolom ditambahkan: `angkatan`, `semester`, `sks_seharusnya`, `selisih_sks`, `lama_studi`, `status_kelulusan`, `label`

---

## 6. Trace Gold → Feature Store

| Tahap | Tabel | Jumlah Baris |
|-------|-------|-------------|
| Gold | `dim_mahasiswa` | 32,703 |
| Feature Store | `training_dataset` (label IS NOT NULL, IP NOT NULL) | **15,599** |
| Feature Store | `inference_dataset` (AKTIF 2022-2024, IP NOT NULL) | **12,244** |

**8 Fitur yang Digunakan:**
1. `jk_enc` (jenis kelamin encoded)
2. `angkatan`
3. `ip`
4. `ipk`
5. `total_sks`
6. `jumlah_mk`
7. `sks_seharusnya`
8. `selisih_sks`

---

## 7. Trace Feature Store → Modeling

| Komponen | Nilai |
|----------|-------|
| Model | GaussianNB |
| Fitur | 8 fitur (di atas) |
| Train/Test Split | 80/20, random_state=42 |
| CV | StratifiedKFold 10-fold |
| Training | 12,479 baris |
| Test | 3,120 baris |
| Best Model | Without SMOTE (CV F1=0.8020) |

**Label Logic:**
- LULUS + lama_studi ≤ 4 tahun → 0 (Tepat Waktu) → masuk TRAINING
- LULUS + lama_studi > 4 tahun → 1 (Terlambat) → masuk TRAINING
- AKTIF 2019-2021 → 1 (Terlambat) → masuk TRAINING
- AKTIF 2022-2024 → NULL → masuk INFERENCE

---

## 8. Trace Modeling → Inference

| Angkatan | Jumlah Inference | Tepat Waktu | Terlambat |
|----------|-----------------|-------------|-----------|
| 2022 | 3,987 | 142 (3.56%) | 3,845 (96.44%) |
| 2023 | 3,985 | 0 (0.00%) | 3,985 (100.00%) |
| 2024 | 4,272 | 0 (0.00%) | 4,272 (100.00%) |
| **Total** | **12,244** | **142 (1.16%)** | **12,102 (98.84%)** |

---

## 9. Tabel Audit Konsistensi

| Tahap | Source | File/Tabel | Jumlah Data | Status |
|-------|--------|------------|-------------|--------|
| Source | Excel | `(asli)req_data_rut (baru).xlsx` | 37,655 (referensi) | OK |
| Bronze | Iceberg | `bronze.data_referensi_mahasiswa` | 37,655 | OK |
| Bronze | Iceberg | `bronze.data_khs` | 28,273 | OK |
| Silver | Iceberg | `silver.silver_mahasiswa` | 32,703 | OK |
| Silver | Iceberg | `silver.silver_khs` | 27,843 | OK |
| Gold | Iceberg | `gold.dim_mahasiswa` | 32,703 | OK |
| Gold | Iceberg | `gold.fact_khs` | 27,843 | OK |
| Feature Store | Iceberg | `feature_store.training_dataset` | 15,599 | OK |
| Feature Store | Iceberg | `feature_store.inference_dataset` | 12,244 | OK |
| Training | Excel | `training_8_features_barulagi.xlsx` | 15,599 | OK |
| Inference | Excel | `inference_2022_2024_barulagi.xlsx` | 12,244 | OK |

---

## 10. Cek File "_barulagi"

### File yang Dibuat

Semua file `_barulagi` merupakan **output/export** dari Iceberg tables, **bukan sumber data**:

| File | Tahap | Sumber | Digunakan untuk Modeling? |
|------|-------|--------|--------------------------|
| `bronze_*_barulagi.xlsx` | Bronze export | Iceberg bronze tables | TIDAK |
| `silver_*_barulagi.xlsx` | Silver export | Iceberg silver tables | TIDAK |
| `gold_*_barulagi.xlsx` | Gold export | Iceberg gold tables | TIDAK |
| `feature_store_*_barulagi.xlsx` | Feature Store export | Iceberg feature_store tables | TIDAK |
| `training_8_features_barulagi.xlsx` | Training export | Iceberg training_dataset | TIDAK (untuk Colab) |
| `inference_2022_2024_barulagi.xlsx` | Inference export | Iceberg inference_dataset | TIDAK (untuk Colab) |

**Penting**: File `_barulagi` adalah salinan data dari Iceberg. Pipeline ML membaca langsung dari Iceberg tables, bukan dari file Excel `_barulagi`.

---

## 11. Perbedaan Antara Versi Dataset

| Aspek | `(asli)req_data_rut.xlsx` | `(asli)req_data_rut (baru).xlsx` | `(asli)req_data_rut (baruu).xlsx` | `(asli)req_data_rut (baruuu).xlsx` |
|-------|--------------------------|----------------------------------|-----------------------------------|-------------------------------------|
| Kolom ID | `ID` | `ID_MHS` | `ID_MHS` | `ID_MHS` |
| Format ID | `MHS64` | `MHS000001` | `MHS000001` | `MHS000001` |
| KHS kolom | 3 | 4 | 4 | 4 |
| Total SKS | 3,843,516 | 3,843,516 | **3,843,025** | **3,841,461** |
| IPK mean | 2.4820 | 2.4820 | 2.4820 | 2.4820 |
| AKTIF | 19,803 | 19,822 | 19,822 | 19,822 |
| Lulus | 13,347 | 13,328 | 13,328 | 13,328 |

**File (baru) dan (1) identik dalam isi data** (hanya berbeda nama file dan ukuran file).  
**File (baruu) dan (baruuu) memiliki Total SKS yang berbeda** dari (baru).

---

## 12. Kesimpulan Final

### DATA ASLI YANG TERAKHIR BENAR-BENAR DIGUNAKAN SISTEM ADALAH:

**Nama File**: `(asli)req_data_rut (baru).xlsx`  
**Path**: `D:\TA\TugasAkhirNita\Data\(asli)req_data_rut (baru).xlsx`  
**Ukuran**: 2,215 KB  
**Tanggal Modifikasi**: 27 Agustus 2026, 08:52:39

### Bukti:

1. **`step1_bronze.py` (baris 8)** membaca `req_data_rut_baru.xlsx` dari container
2. **File yang di-copy ke container**: `(asli)req_data_rut (baru).xlsx` → `req_data_rut_baru.xlsx`
3. **`full_pipeline_final.py` (baris 19)** menegaskan: "BRONZE (already loaded via step1_bronze.py)"
4. **Jumlah data Bronze**: 37,655 baris (sesuai dengan filebaru)
5. **Kolom**: `ID_MHS` (bukan `ID` seperti file original)
6. **Status distribusi**: AKTIF=19,822, Lulus=13,328 (sesuai filebaru)

### Alur Data:

```
(asli)req_data_rut (baru).xlsx
  ↓ [step1_bronze.py: pd.read_excel → parquet → Spark → Iceberg]
Bronze: data_referensi_mahasiswa (37,655), data_khs (28,273)
  ↓ [full_pipeline_final.py → silver.process_all_tables()]
Silver: silver_mahasiswa (32,703), silver_khs (27,843)
  ↓ [full_pipeline_final.py → gold.process_gold_fact_khs() + process_gold_dim_mahasiswa()]
Gold: dim_mahasiswa (32,703), fact_khs (27,843)
  ↓ [full_pipeline_final.py → feature_store.run_feature_store()]
Feature Store: training_dataset (15,599), inference_dataset (12,244)
  ↓ [full_pipeline_final.py → ml training + inference]
Training: 15,599 baris, 8 fitur, label (0/1)
Inference: 12,244 baris, prediksi (TW/TL)
  ↓ [export_all_barulagi.py]
Excel: *_barulagi.xlsx (untuk Google Colab)
```

### Catatan Penting:

- **File yang DIGUNAKAN**: `(asli)req_data_rut (baru).xlsx`
- **File yang TIDAK digunakan**: `(asli)req_data_rut.xlsx` (original), `(asli)req_data_rut (1).xlsx`, `(asli)req_data_rut (baruu).xlsx`, `(asli)req_data_rut (baruuu).xlsx`
- **Production Airflow DAG** menunjuk ke `(asli)req_data_rut (1).xlsx`, tetapi pipeline terakhir dijalankan secara manual menggunakan `step1_bronze.py` yang membaca `(asli)req_data_rut (baru).xlsx`
- **File (baru) dan (1)** memiliki isi data yang identik (Total SKS sum sama: 3,843,516)
- **File (baruu) dan (baruuu)** memiliki Total SKS yang berbeda, yang berarti **data数值不同**

---

## 13. Rekomendasi

1. **Gunakan `(asli)req_data_rut (baru).xlsx`** sebagai file data asli resmi
2. **Update `step1_bronze.py`** jika ingin menggunakan file yang berbeda
3. **Update `prediction_pipeline.py`** jika ingin Airflow DAG menggunakan file yang sama
4. **Hapus file duplikat** yang tidak digunakan untuk menghindari kebingungan
5. **Dokumentasikan** file data asli yang digunakan secara eksplisit di README
