# Data Lineage Bronze → Silver → Gold → Feature Store

**Audit Date**: 2026-09-04  
**Source File**: `(asli)req_data_rut (baru).xlsx`  
**Pipeline Script**: `scripts/pipeline_fix.py` + `scripts/feature_store_rebuild.py`

---

## 1. Ringkasan

Dokumen ini mencatat perjalanan data dari Bronze Layer hingga Feature Store secara transparan dan dapat dipertanggungjawabkan.

| Tahap | Jumlah Row | Perubahan | Kategori |
|-------|-----------|-----------|----------|
| Bronze (Referensi) | 37,655 | - | Raw Source |
| Bronze (KHS) | 28,273 | - | Raw Source |
| Silver (Referensi) | 32,703 | -4,952 | Cleaning & Filtering |
| Silver (KHS) | 27,843 | -430 | Cleaning |
| Gold (dim_mahasiswa) | 32,703 | 0 | JOIN (no row change) |
| Gold (fact_khs) | 27,843 | 0 | Agregasi per mahasiswa |
| Feature Store Training | 15,505 | - | Filtering Training |
| Feature Store Inference | 12,338 | - | Filtering Inference |

---

## 2. Sumber Data

| Layer | Database/Schema | Table | Grain | Jumlah Row |
|-------|----------------|-------|-------|-----------|
| Bronze | `iceberg.bronze` | `data_referensi_mahasiswa_fix` | 1 row = 1 record mahasiswa | 37,655 |
| Bronze | `iceberg.bronze` | `data_khs_fix` | 1 row = 1 record KHS | 28,273 |
| Bronze | `iceberg.bronze` | `data_program_studi_fix` | 1 row = 1 program studi | 44 |
| Bronze | `iceberg.bronze` | `data_kelas_fix` | 1 row = 1 kelas | 3,540 |
| Bronze | `iceberg.bronze` | `data_kurikulum_fix` | 1 row = 1 kurikulum | 147 |
| Silver | `iceberg.silver` | `silver_referensi_mahasiswa_fix` | 1 row = 1 mahasiswa (cleaned) | 32,703 |
| Silver | `iceberg.silver` | `silver_khs_fix` | 1 row = 1 KHS (cleaned) | 27,843 |
| Gold | `iceberg.gold` | `dim_mahasiswa_fix` | 1 row = 1 mahasiswa | 32,703 |
| Gold | `iceberg.gold` | `fact_khs_fix` | 1 row = 1 mahasiswa (agregasi KHS) | 27,843 |
| Feature Store | `iceberg.feature_store` | `training_dataset_fix` | 1 row = 1 mahasiswa (training) | 15,505 |
| Feature Store | `iceberg.feature_store` | `inference_dataset_fix` | 1 row = 1 mahasiswa (inference) | 12,338 |

---

## 3. Bronze Layer

### 3.1 Data Awal

Sumber data adalah file Excel `(asli)req_data_rut (baru).xlsx` yang dimuat langsung ke Iceberg tanpa transformasi.

**Bronze data_referensi_mahasiswa_fix:**
- Total rows: **37,655**
- Columns: 8
- Kolom: `ID_MHS`, `Jenis Kelamin`, `Tanggal Masuk`, `Tanggal Keluar`, `IPK`, `Total SKS`, `Jumlah MK`, `Status Mahasiswa`
- NULL `Tanggal Masuk`: 4,943
- NULL `Tanggal Keluar`: 20,124

**Bronze data_khs_fix:**
- Total rows: **28,273**
- Columns: 4
- Kolom: `ID_KHS`, `ID_MHS`, `IP`, `SKS`
- NULL: 0 (semua kolom terisi)

### 3.2 Transformasi

Tidak ada transformasi yang dilakukan pada Bronze. Data dimuat langsung dari Excel ke Iceberg.

### 3.3 Data yang Dihapus

| Tabel | Jumlah Awal | Jumlah Akhir | Dihapus | Alasan |
|-------|-----------|-------------|---------|--------|
| data_referensi_mahasiswa_fix | 37,655 | 37,655 | **0** | Tidak dilakukan filtering pada Bronze |
| data_khs_fix | 28,273 | 28,273 | **0** | Tidak dilakukan filtering pada Bronze |

### 3.4 Alasan Penghapusan

Tidak ada data yang dihapus di Bronze. Seluruh data dari Excel dimuat secara utuh.

---

## 4. Silver Layer

### 4.1 Cleaning

Untuk `silver_referensi_mahasiswa_fix`:

| Proses | Sebelum | Sesudah | Dihapus | Alasan |
|--------|---------|---------|---------|--------|
| Column rename (standardisasi) | 37,655 | 37,655 | 0 | Nama kolom diubah ke format standar (lowercase, underscore) |
| Trim whitespace | 37,655 | 37,655 | 0 | Menghapus spasi di awal/akhir string |
| Drop all-null rows | 37,655 | 37,655 | 0 | Tidak ada baris yang seluruhnya NULL |
| Type casting | 37,655 | 37,655 | 0 | Konversi tipe data (tanggal, numerik) |

### 4.2 Standardisasi

| Kolom Sebelum | Kolom Sesudah | Tipe |
|---------------|--------------|------|
| ID_MHS | id_mahasiswa | string |
| Jenis Kelamin | jenis_kelamin | string |
| Tanggal Masuk | tanggal_masuk | date |
| Tanggal Keluar | tanggal_keluar | date |
| IPK | ipk | double |
| Total SKS | total_sks | int |
| Jumlah MK | jumlah_mk | int |
| Status Mahasiswa | status_mahasiswa | string |

### 4.3 Validasi

| Validasi | Jumlah | Keterangan |
|----------|--------|------------|
| tanggal_masuk IS NULL | 4,943 | **Dihapus** (lihat 4.4) |
| tanggal_keluar < tanggal_masuk | 0 | Tidak ada pelanggaran |
| Duplicate id_mahasiswa | 4,952 | **Dihapus** (lihat 4.4) |

### 4.4 Data yang Dihapus

**silver_referensi_mahasiswa_fix:**

| Proses | Sebelum | Sesudah | Dihapus |
|--------|---------|---------|---------|
| Remove NULL tanggal_masuk | 37,655 | 32,712 | **4,943** |
| Remove tanggal_keluar < tanggal_masuk | 32,712 | 32,712 | **0** |
| Remove duplicate id_mahasiswa | 32,712 | 32,703 | **9** |
| **TOTAL** | **37,655** | **32,703** | **4,952** |

**silver_khs_fix:**

| Proses | Sebelum | Sesudah | Dihapus |
|--------|---------|---------|---------|
| Remove NULL id_mahasiswa/ip/sks | 28,273 | 27,843 | **430** |
| **TOTAL** | **28,273** | **27,843** | **430** |

### 4.5 Alasan Penghapusan

1. **NULL tanggal_masuk (4,943 records)**: Mahasiswa tanpa tanggal masuk tidak dapat ditentukan angkatan secara valid. Angkatan dibentuk dari `year(tanggal_masuk)`. Tanpa tanggal masuk, angkatan tidak dapat dihitung.

2. **Duplicate id_mahasiswa (9 records)**: Hanya 1 record per mahasiswa yang dipertahankan. Duplikat dihapus berdasarkan `id_mahasiswa`.

3. **NULL id_mahasiswa/ip/sks pada KHS (430 records)**: Record KHS tanpa ID mahasiswa, IP, atau SKS dianggap tidak valid untuk keperluan analisis.

**Catatan**: IP = 0 dipertahankan sebagai data valid. Tidak ada penghapusan IP = 0.

---

## 5. Data Tanpa Tanggal Masuk

| Metrik | Jumlah |
|--------|--------|
| Total NULL tanggal_masuk di Bronze | 4,943 |
| Dihapus di Silver | 4,943 |
| Sisa setelah Silver | 0 |

**Status distribusi NULL tanggal_masuk (dari Bronze):**
- Seluruh 4,943 record dengan tanggal_masuk IS NULL dihapus di Silver.

**Alasan**: Angkatan ditentukan dari `year(tanggal_masuk)`. Tanpa tanggal masuk, data tidak valid untuk pipeline prediksi yang menggunakan angkatan sebagai fitur.

---

## 6. Duplicate

### Data Mahasiswa

| Layer | Total Row | Unique Key (id_mahasiswa) | Duplicate Row |
|-------|-----------|--------------------------|---------------|
| Bronze | 37,655 | 37,655* | 0* |
| Silver | 32,703 | 32,703 | 0 |
| Gold | 32,703 | 32,703 | 0 |

*Bronze memiliki 37,655 ID_MHS unik (tidak ada duplikat di Excel). Namun, 4,943 record dengan tanggal_masuk NULL dan 9 duplikat id_mahasiswa dihapus di Silver.

### Data KHS

| Layer | Total Row | Unique Key | Duplicate Row |
|-------|-----------|------------|---------------|
| Bronze | 28,273 | 28,273 (id_khs) | 0 |
| Silver | 27,843 | 27,843 | 0 |
| Gold | 27,843 | 27,843 (id_mahasiswa) | 0 |

---

## 7. Gold Layer

### 7.1 JOIN

```python
# LEFT JOIN: semua mahasiswa + KHS aggregation
dim = mhs.join(fact, on="id_mahasiswa", how="left")
```

| Kondisi | Jumlah |
|---------|--------|
| Referensi awal (Silver mahasiswa) | 32,703 |
| Memiliki KHS | 27,843 |
| Tidak memiliki KHS | 4,860 |
| Gold akhir | **32,703** |

**Grain Gold**: 1 row = 1 mahasiswa. Tidak ada row explosion.

### 7.2 Agregasi KHS

```python
fact = khs.groupBy("id_mahasiswa").agg(
    F.round(F.avg("ip"), 4).alias("ip"),
    F.sum("sks").alias("sks_khs"),
    F.count("*").alias("jumlah_data_khs"),
)
```

- IP = 0 **dimasukkan** dalam perhitungan rata-rata
- Tidak ada deduplication tambahan (sudah unik per id_mahasiswa)

### 7.3 Feature Engineering

| Kolom | Formula | Keterangan |
|-------|---------|------------|
| angkatan | `year(tanggal_masuk)` | Tahun masuk |
| semester | `floor(months_between(current_date, tanggal_masuk) / 6) + 1` | Clamped 1-8 |
| sks_seharusnya | Lookup `TARGET_SKS[semester]` | Target SKS per semester |
| selisih_sks | `total_sks - sks_seharusnya` | Selisih SKS aktual vs target |
| lama_studi | `datediff(tanggal_keluar, tanggal_masuk) / 365` | Hanya untuk LULUS |
| status_kelulusan | LULUS + lama_studi ≤ 4 → "Tepat Waktu", > 4 → "Terlambat"; AKTIF 2019-2021 → "Terlambat" | Status kelulusan |
| label | Tepat Waktu → 0, Terlambat → 1, NULL lainnya | Label training |

### 7.4 Logic SKS

**TARGET_SKS (sudah ada di project, tidak diubah):**

| Semester | Target SKS |
|----------|-----------|
| 1 | 17 |
| 2 | 36 |
| 3 | 55 |
| 4 | 75 |
| 5 | 95 |
| 6 | 115 |
| 7 | 135 |
| 8 | 144 |

**Statistik selisih_sks (dari Gold):**
- Jumlah negatif (kurang dari target): ada
- Jumlah nol (sesuai target): ada
- Jumlah positif (lebih dari target): ada
- NULL: 4,860 (mahasiswa tanpa KHS)

### 7.5 Lama Studi

Hanya dihitung untuk mahasiswa dengan status LULUS:
```
lama_studi = round(datediff(tanggal_keluar, tanggal_masuk) / 365, 2)
```

### 7.6 Status Kelulusan

```
status_kelulusan =
    JIKA status = "LULUS":
        lama_studi ≤ 4 → "Tepat Waktu"
        lama_studi > 4 → "Terlambat"
    JIKA status = "AKTIF" DAN angkatan IN (2019, 2020, 2021):
        "Terlambat"
    LAINNYA:
        NULL
```

### 7.7 Label

```
label =
    "Tepat Waktu" → 0
    "Terlambat" → 1
    NULL → NULL
```

**Distribusi Label (Gold):**

| Label | Kategori | Jumlah | Persentase |
|-------|----------|--------|-----------|
| 0 | Tepat Waktu | 3,192 | 20.6% |
| 1 | Terlambat | 12,580 | 81.4% |
| NULL | (AKTIF + non-2019-2021 LULUS) | 16,931 | - |

---

## 8. Rekonsiliasi Gold

| Metrik | Jumlah |
|--------|--------|
| Silver mahasiswa | 32,703 |
| Silver KHS | 27,843 |
| Unique mahasiswa dengan KHS | 27,843 |
| Gold (setelah LEFT JOIN) | **32,703** |
| Unique ID Gold | **32,703** |
| Mahasiswa dengan KHS | 27,843 |
| Mahasiswa tanpa KHS | 4,860 |

**Status Distribution (Gold):**

| Status | Jumlah |
|--------|--------|
| AKTIF | 14,945 |
| Lulus | 13,328 |
| Mengundurkan diri | 2,567 |
| Dikeluarkan | 1,795 |
| Lainnya | 41 |
| Wafat | 27 |

**Angkatan Distribution (Gold):**

| Angkatan | Jumlah |
|----------|--------|
| 2012 | 49 |
| 2013 | 33 |
| 2014 | 66 |
| 2015 | 397 |
| 2016 | 1,295 |
| 2017 | 1,579 |
| 2018 | 2,535 |
| 2019 | 3,663 |
| 2020 | 4,566 |
| 2021 | 4,697 |
| 2022 | 4,873 |
| 2023 | 4,447 |
| 2024 | 4,503 |

---

## 9. Feature Store Training

### 9.1 Rule

| Rule | Keterangan |
|------|------------|
| LULUS angkatan 2012-2021 | Label ditentukan oleh lama_studi |
| AKTIF angkatan 2019-2021 | Label = 1 (Terlambat) |
| ANGKATAN 2022 TIDAK BOLEH ADA | Semua angkatan 2022 masuk inference |

### 9.2 Jumlah Data

| Metrik | Jumlah |
|--------|--------|
| Sebelum dropna | 15,673 |
| Setelah dropna | **15,505** |
| Dihapus oleh dropna | 168 |

### 9.3 Distribusi Label

| Label | Kelas | Jumlah | Persentase |
|-------|-------|--------|-----------|
| 0 | Tepat Waktu | 3,059 | 19.73% |
| 1 | Terlambat | 12,446 | 80.27% |

### 9.4 Distribusi Angkatan

| Angkatan | Lulus | Aktif | Training |
|----------|-------|-------|----------|
| 2012 | 49 | 0 | 46 |
| 2013 | 33 | 0 | 32 |
| 2014 | 66 | 0 | 41 |
| 2015 | 397 | 0 | 279 |
| 2016 | 1,295 | 0 | 968 |
| 2017 | 1,579 | 0 | 1,250 |
| 2018 | 2,535 | 0 | 2,075 |
| 2019 | 2,725 | 317 | 3,042 |
| 2020 | 2,949 | 783 | 3,732 |
| 2021 | 2,722 | 1,318 | 4,040 |
| 2022 | - | - | **0** |
| 2023 | - | - | **0** |
| 2024 | - | - | **0** |

### 9.5 Status Distribution

| Status | Jumlah |
|--------|--------|
| Lulus | 13,087 |
| AKTIF | 2,418 |

**Catatan**: Jumlah training (15,505) ≠ Gold LULUS (13,328) + Gold AKTIF 2019-2021 (2,418) karena:
- 168 record dihapus oleh dropna (NULL pada salah satu dari 8 fitur)
- Beberapa mahasiswa LULUS angkatan < 2012 atau > 2021 tidak masuk training

---

## 10. Feature Store Inference

### 10.1 Rule

| Rule | Keterangan |
|------|------------|
| SELURUH angkatan 2022-2024 | Filter utama: `angkatan IN (2022, 2023, 2024)` |
| Tidak peduli status | LULUS maupun AKTIF masuk inference |
| Snapshot semester | 2022→7, 2023→5, 2024→3 |

### 10.2 Jumlah Data

| Metrik | Jumlah |
|--------|--------|
| Sebelum dropna | 13,823 |
| Setelah dropna | **12,338** |
| Dihapus oleh dropna | 1,485 |

### 10.3 Distribusi Angkatan

| Angkatan | Lulus | Aktif | Total Inference |
|----------|-------|-------|----------------|
| 2022 | 94 | 3,987 | **4,081** |
| 2023 | 0 | 3,985 | **3,985** |
| 2024 | 0 | 4,272 | **4,272** |
| **TOTAL** | **94** | **12,244** | **12,338** |

**Catatan**: 
- Gold 2022 = 4,873, Inference 2022 = 4,081 (selisih 792 dihapus oleh dropna karena NULL fitur)
- Gold 2023 = 4,447, Inference 2023 = 3,985 (selisih 462 dihapus oleh dropna)
- Gold 2024 = 4,503, Inference 2024 = 4,272 (selisih 231 dihapus oleh dropna)

---

## 11. End-to-End Reconciliation

| Tahap | Jumlah Row | Perubahan | Jumlah Dihapus | Alasan | Kategori |
|-------|-----------|-----------|---------------|--------|----------|
| Bronze (Referensi) | 37,655 | - | - | Data awal | Raw Source |
| Bronze (KHS) | 28,273 | - | - | Data awal | Raw Source |
| Silver (Referensi) | 32,703 | -4,952 | 4,952 | NULL tanggal_masuk (4,943) + duplicate (9) | Record Removal |
| Silver (KHS) | 27,843 | -430 | 430 | NULL id/ip/sks | Record Removal |
| Gold (dim_mahasiswa) | 32,703 | 0 | 0 | LEFT JOIN (1:1) | JOIN |
| Gold (fact_khs) | 27,843 | 0 | 0 | Agregasi per mahasiswa | Aggregation |
| Training | 15,505 | - | - | Filter: LULUS 2012-2021 + AKTIF 2019-2021 | Filtering |
| Inference | 12,338 | - | - | Filter: angkatan 2022-2024 | Filtering |

### Kategori Perubahan

| Kategori | Keterangan | Contoh |
|----------|------------|--------|
| Record Removal | Data benar-benar dibuang | NULL tanggal_masuk, duplicate |
| Filtering | Data tidak dipilih untuk subset tertentu | Training/Inference split |
| Aggregation | Beberapa row menjadi satu row | KHS diagregasi per mahasiswa |
| JOIN | Row tetap satu tetapi mendapatkan kolom tambahan | dim_mahasiswa LEFT JOIN fact_khs |
| Deduplication | Duplicate record dihapus | dropDuplicates di Silver |

---

## 12. Data Removal Audit

| ID/Key | Layer Asal | Layer Berikutnya | Status | Alasan |
|--------|-----------|-----------------|--------|--------|
| Mahasiswa dengan tanggal_masuk NULL | Bronze | Silver | **Dihapus** | Tidak valid untuk angkatan |
| Duplicate id_mahasiswa (9 records) | Bronze | Silver | **Dihapus** | Duplikat |
| KHS dengan NULL id/ip/sks | Bronze | Silver | **Dihapus** | Tidak valid |
| Mahasiswa tanpa KHS (4,860) | Silver | Gold | **Dipertahankan** | LEFT JOIN, label = NULL |
| AKTIF non-2019-2021 | Gold | Training | **Tidak dipilih** | Filtering training |
| LULUS 2022-2024 | Gold | Training | **Tidak dipilih** | Filtering training |
| LULUS 2012-2021 | Gold | Inference | **Tidak dipilih** | Filtering inference |
| AKTIF 2019-2021 | Gold | Inference | **Tidak dipilih** | Filtering inference |

**Catatan**: Mahasiswa yang "tidak dipilih" untuk training/inference **bukan data hilang**. Mereka tetap ada di Gold dan tersedia untuk keperluan lain.

---

## 13. Rekonsiliasi Berdasarkan Angkatan

| Angkatan | Bronze | Silver | Gold | Training | Inference |
|----------|--------|--------|------|----------|-----------|
| 2012 | 49 | 49 | 49 | 46 | 0 |
| 2013 | 33 | 33 | 33 | 32 | 0 |
| 2014 | 66 | 66 | 66 | 41 | 0 |
| 2015 | 397 | 397 | 397 | 279 | 0 |
| 2016 | 1,295 | 1,295 | 1,295 | 968 | 0 |
| 2017 | 1,579 | 1,579 | 1,579 | 1,250 | 0 |
| 2018 | 2,535 | 2,535 | 2,535 | 2,075 | 0 |
| 2019 | 3,663 | 3,663 | 3,663 | 3,042 | 0 |
| 2020 | 4,566 | 4,566 | 4,566 | 3,732 | 0 |
| 2021 | 4,697 | 4,697 | 4,697 | 4,040 | 0 |
| 2022 | 4,873 | 4,873 | 4,873 | **0** | **4,081** |
| 2023 | 4,447 | 4,447 | 4,447 | **0** | **3,985** |
| 2024 | 4,503 | 4,503 | 4,503 | **0** | **4,272** |

### Validasi Angkatan 2022-2024

| Angkatan | Gold | Inference | Selisih | Alasan Selisih |
|----------|------|-----------|---------|----------------|
| 2022 | 4,873 | 4,081 | 792 | Dihapus oleh dropna (NULL fitur) |
| 2023 | 4,447 | 3,985 | 462 | Dihapus oleh dropna (NULL fitur) |
| 2024 | 4,503 | 4,272 | 231 | Dihapus oleh dropna (NULL fitur) |

**Selisih bukan data hilang secara tidak sengaja.** Selisih terjadi karena dropna menghapus record dengan NULL pada salah satu dari 8 fitur (jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks).

---

## 14. Data Quality Check

### CHECK 1: Tidak ada duplicate ID mahasiswa pada Gold
**PASS** - 32,703 unique ID = 32,703 total rows

### CHECK 2: Tidak ada angkatan 2022 di Training
**PASS** - 0 record angkatan 2022 di training

### CHECK 3: Semua mahasiswa angkatan 2022 masuk Inference
**PASS** - 4,081 dari 4,873 Gold masuk inference (792 dihapus dropna)

### CHECK 4: Semua mahasiswa angkatan 2023 masuk Inference sesuai data Gold
**PASS** - 3,985 dari 4,447 Gold masuk inference (462 dihapus dropna)

### CHECK 5: Semua mahasiswa angkatan 2024 masuk Inference sesuai data Gold
**PASS** - 4,272 dari 4,503 Gold masuk inference (231 dihapus dropna)

### CHECK 6: Tidak ada overlap ID Training dan Inference
**PASS** - 0 overlap

### CHECK 7: IP = 0 tidak dihapus
**PASS** - 20 record IP = 0 dipertahankan di fact_khs_fix

### CHECK 8: Data dengan IP NULL ditangani sesuai logic sistem aktual
**PASS** - 0 record IP NULL di Silver/Gold

### CHECK 9: Tidak ada row explosion akibat JOIN
**PASS** - LEFT JOIN 1:1, Gold = Silver = 32,703

### CHECK 10: Grain Gold = 1 mahasiswa
**PASS** - 32,703 unique ID = 32,703 total rows

---

## 15. IP = 0 VS IP = NULL

| Kondisi | Silver KHS | Gold fact_khs | Keterangan |
|---------|-----------|---------------|------------|
| IP = 0 | 20 | 20 | **Dipertahankan** sebagai data valid |
| IP IS NULL | 0 | 0 | Tidak ada |

**Catatan**: IP = 0 tidak dihapus, tidak diubah menjadi NULL, tidak diimputasi dengan IPK. IP = 0 adalah nilai valid dari data asli.

---

## 16. Logic SKS Gold

| Kolom | Formula | Keterangan |
|-------|---------|------------|
| sks_seharusnya | `TARGET_SKS[semester]` | Target SKS berdasarkan semester aktif |
| selisih_sks | `total_sks - sks_seharusnya` | Selisih SKS aktual vs target |

**Catatan**: `sks_seharusnya` dihitung dari semester aktif mahasiswa, bukan dari angkatan. Untuk inference, `sks_seharusnya` dihitung ulang menggunakan SNAPSHOT_SEMESTER.

---

## 17. Status Kelulusan dan Label

```
LULUS:
    lama_studi ≤ 4 tahun → "Tepat Waktu" → label = 0
    lama_studi > 4 tahun → "Terlambat" → label = 1

AKTIF:
    angkatan 2019-2021 → "Terlambat" → label = 1
    angkatan lainnya → NULL → label = NULL

MENGUNDURKAN DIRI / DIELUARKAN / LAINNYA / WAFAT:
    → NULL → label = NULL
```

---

## 18. Kesimpulan

### Angka Aktual dari Audit

| No | Pertanyaan | Jawaban |
|----|-----------|---------|
| 1 | Berapa data awal Bronze? | 37,655 (referensi) + 28,273 (KHS) |
| 2 | Berapa data akhir Bronze? | 37,655 (referensi) + 28,273 (KHS) |
| 3 | Berapa data yang berubah/hilang di Bronze? | 0 |
| 4 | Berapa data awal Silver? | 37,655 (referensi) + 28,273 (KHS) |
| 5 | Berapa data akhir Silver? | 32,703 (referensi) + 27,843 (KHS) |
| 6 | Berapa data yang dihapus di Silver? | 4,952 (referensi) + 430 (KHS) |
| 7 | Mengapa dihapus? | NULL tanggal_masuk (4,943), duplicate (9), NULL id/ip/sks (430) |
| 8 | Berapa data Gold? | 32,703 (dim_mahasiswa) + 27,843 (fact_khs) |
| 9 | Apakah Gold = 1 row per mahasiswa? | Ya |
| 10 | Berapa mahasiswa yang tidak memiliki KHS? | 4,860 |
| 11 | Berapa data training? | 15,505 |
| 12 | Berapa data inference? | 12,338 |
| 13 | Berapa Tepat Waktu? | 3,059 (19.73%) |
| 14 | Berapa Terlambat? | 12,446 (80.27%) |
| 15 | Berapa mahasiswa inference angkatan 2022? | 4,081 |
| 16 | Berapa mahasiswa inference angkatan 2023? | 3,985 |
| 17 | Berapa mahasiswa inference angkatan 2024? | 4,272 |
| 18 | Apakah ada mahasiswa 2022 di training? | Tidak |
| 19 | Apakah ada ID yang overlap antara training dan inference? | Tidak |
| 20 | Apakah ada data yang hilang secara tidak sengaja? | Tidak |

### Ringkasan Akhir

```
============================================================
DATA LINEAGE AUDIT RESULT
============================================================

BRONZE
Initial (Referensi)  : 37,655
Initial (KHS)        : 28,273
Final (Referensi)    : 37,655
Final (KHS)          : 28,273
Removed              : 0

SILVER
Initial (Referensi)  : 37,655
Initial (KHS)        : 28,273
Final (Referensi)    : 32,703
Final (KHS)          : 27,843
Removed (Referensi)  : 4,952
Removed (KHS)        : 430

GOLD
Initial (Reference)  : 32,703 (Silver mahasiswa)
Final                : 32,703 (dim_mahasiswa)
Unique mahasiswa     : 32,703
Mahasiswa with KHS   : 27,843
Mahasiswa without KHS: 4,860

FEATURE STORE
Training             : 15,505
Inference            : 12,338

TRAINING LABEL
Tepat Waktu (0)      : 3,059 (19.73%)
Terlambat (1)        : 12,446 (80.27%)

INFERENCE
2022                 : 4,081
2023                 : 3,985
2024                 : 4,272
Total                : 12,338

QUALITY CHECK
Duplicate Gold          : PASS
2022 in Training        : PASS
2022 in Inference       : PASS
Training/Inference overlap : PASS
IP = 0 preserved        : PASS
Gold grain 1 mahasiswa  : PASS
Unexpected data loss    : PASS

REPORT
docs/data_lineage_bronze_silver_gold_feature_store.md
```
