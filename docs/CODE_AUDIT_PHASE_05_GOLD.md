# Phase 5 — Gold Layer Audit

Audit statis (tanpa menjalankan aplikasi/service) pada **Gold Layer** project Tugas Akhir:

> **"Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis Machine Learning"**

Project utama: `D:\TugasAkhirNita\`

Acuan arsitektur: **Docker-based** (Spark di dalam Docker; Bronze → Silver → Gold → Feature Store → ML). Hasil Phase 2 (Spark+Iceberg+Docker), Phase 3 (Bronze), Phase 4 (Silver) dipakai sebagai konteks.

---

## 1. Scope

- Audit pada `backend/gold/` (`gold.py`, `gold_mahasiswa.py`, `gold_prodi.py`, `gold_kurikulum.py`)
- Dependency yang dibaca untuk memahami Gold: `backend/silver/silver.py`, `backend/bronze/bronze.py`, `backend/spark/session.py`, `backend/config/settings.py`
- Script pemeriksa Gold: `scripts/test_gold.py`, `scripts/check_gold.py`
- **Feature Store dibaca hanya untuk memahami output contract Gold** (`training_dataset.py`, `inference_dataset.py`) — tidak diubah
- ML (`train.py`, `data_preparation.py`) dan Postgres sink dibaca secukupnya untuk memverifikasi kontrak kolom — **tidak diaudit mendalam, tidak diubah**

Airflow, Trino, Superset, ML, Feature Store **tidak** diubah.

---

## 2. Gold Architecture

```text
Silver (iceberg.silver.data_referensi_mahasiswa / data_program_studi / data_kurikulum)
        ↓  (spark.table ... .silver.<table>)
Gold Layer
        ↓  gold_mahasiswa: casting + feature engineering + label
        ↓  gold_prodi     : passthrough  (silver sudah bersih)
        ↓  gold_kurikulum : passthrough
        ↓  df.writeTo(iceberg.gold.<table>).using("iceberg").createOrReplace()
Iceberg (catalog 'iceberg' = Hive Metastore) → MinIO (s3a://warehouse/iceberg/gold/...)
        ↓
Feature Store (membaca gold.gold_mahasiswa → training_dataset / inference_dataset)
        ↓
ML (membaca feature_store.training_dataset)
```

---

## 3. Gold Tables

| Gold Table | Source | Grain | Key | Purpose |
|---|---|---|---|---|
| `gold_mahasiswa` | `silver.data_referensi_mahasiswa` | 1 row = 1 mahasiswa (tidak ada join/groupBy — grain mengikuti Silver 1:1) | Tidak ada key eksplisit yang dipertahankan (NIM tidak dipakai sebagai key/grain) | Feature engineering + label kelulusan untuk ML & analitik |
| `gold_program_studi` | `silver.data_program_studi` | 1 row = 1 program studi (passthrough) | (dari data sumber) | Tabel domain prodi |
| `gold_kurikulum` | `silver.data_kurikulum` | 1 row = 1 kurikulum (passthrough) | (dari data sumber) | Tabel domain kurikulum; memengaruhi konstanta `jumlah_sks_kurikulum` |

**Grain determinasi (gold_mahasiswa):** tidak ada `groupBy`, `join`, `distinct`, `window` di `gold_mahasiswa.py`; setiap transformasi adalah `withColumn` per-row → grain **1 row = 1 row Silver**. Duplicate baris di Silver tetap duplicate di Gold (tidak diperbaiki di sini — sesuai boundary Phase 4).

---

## 4. Join Analysis

| Join | Kiri | Kanan | Key | Jenis | Tujuan | Potensi |
|---|---|---|---|---|---|---|
| (implisit, bukan `join()`) | `data_referensi_mahasiswa` | `data_kurikulum` | `jumlah_sks_total` diambil via `.first()` — konstanta skalar, **bukan join per-row** | — | Mendapatkan `jumlah_sks_kurikulum` untuk menghitung `persentase_sks` | Tidak ada row multiplication, tidak ada kehilangan mahasiswa |

**Catatan:** `jumlah_sks_kurikulum` diambil dari **baris pertama** tabel kurikulum (`kurikulum.select("jumlah_sks_total").first()[0]`).

- Bila tabel kurikulum **kosong** atau kolom NULL → `None` → `persentase_sks` menjadi NULL/error → **NEEDS RUNTIME VERIFICATION / data aktual**.
- Bila ada **lebih dari satu kurikulum** (mis. per prodi/angkatan) → konstanta tunggal dipakai untuk semua mahasiswa.
- Keberadaan/keunikan satu kurikulum hanya bisa dibuktikan dari data aktual → **NEEDS RUNTIME VERIFICATION**.

---

## 5. Aggregation Analysis

| Aggregation | Key | Metric | Level | Alasan dari kode |
|---|---|---|---|---|
| `df.groupBy("status_mahasiswa").count().show()` (gold.py:152) | status_mahasiswa | count | **diagnostik log saja** — tidak mengubah df | Verifikasi distribusi status |
| `df.groupBy("status_kelulusan").count().show()` (gold.py:158) | status_kelulusan | count | **diagnostik log saja** — tidak mengubah df | Verifikasi distribusi kelulusan |

Kedua agregasi adalah **show() diagnostik**, hasilnya tidak disimpan dan tidak mengubah grain. **Tidak ada aggregation bisnis (min/max/stddev/sum per prodi/periode) di Gold** — tabel prodi/kurikulum murni passthrough. Ini sesuai desain; agregasi bisnis berada di luar scope Gold saat ini.

---

## 6. Feature Engineering

| Feature | Source | Transformation | Potential Leakage |
|---|---|---|---|
| `ipk` (double) | `silver.ipk` | `cast("double")` | **Potensi.** IPK yang dipakai untuk mahasiswa LULUS adalah IPK final (outcome sudah terjadi). |
| `total_sks` (int) | `silver.total_sks` | `cast("int")` | **Potensi.** Total SKS final mahasiswa yang sudah lulus. |
| `jumlah_mk` (int) | `silver.jumlah_mk` | `cast("int")` | **Potensi.** Jumlah MK final. |
| `tanggal_masuk` (date) | `silver.tanggal_masuk` | `cast("date")` | Digunakan hanya untuk lama studi (bukan feature langsung). |
| `tanggal_keluar` (date) | `silver.tanggal_keluar` | `cast("date")` | Digunakan untuk lama studi **hanya saat mahasiswa sudah keluar/lulus** (lihat §8). |
| `lama_studi_bulan` | `tanggal_masuk`, `tanggal_keluar`, `current_date` | `when(tanggal_keluar isNull, ceil(months_between(current_date(), tanggal_masuk))).otherwise(ceil(months_between(tanggal_keluar, tanggal_masuk)))` | Tidak di-output ke FS, hanya intermediate. Untuk yang lulus → memakai tanggal keluar (outcome). |
| `estimasi_semester` | `lama_studi_bulan` | `ceil(lama_studi_bulan / 6)` | **Krusial — dipakai sebagai feature ML** (`feature_store.*`) | lihat §10 |
| `persentase_sks` | `total_sks`, `jumlah_sks_kurikulum` | `(total_sks / jumlah_sks_kurikulum) * 100` | **Potensi.** total_sks final. |
| `status_kelulusan` (label) | `status_mahasiswa`, `estimasi_semester` | `when(status=="LULUS", when(estimasi<=8,"Tepat Waktu").otherwise("Terlambat")).otherwise(None)` | Target/label — bukan feature. |

Kolom yang benar-benar menjadi feature ML (dari `feature_store.training_dataset.py` & `data_preparation.py`): `jenis_kelamin`, `estimasi_semester`, `ipk`, `total_sks`, `jumlah_mk`, `persentase_sks`.

---

## 7. Target / Label

| Target | Source | Logic | Classes |
|---|---|---|---|
| `status_kelulusan` | `status_mahasiswa`, `estimasi_semester` | `upper(trim(status_mahasiswa)) == "LULUS"` DAN: `estimasi_semester <= 8` → `"Tepat Waktu"`; `estimasi_semester > 8` → `"Terlambat"`; selain itu → `NULL` | `Tepat Waktu` / `Terlambat` / `NULL` |

- Sesuai dengan dokumentasi (`ALUR_PENGERJAAN.md:189-192`, `REVIEW_PROJECT.md:220-223`). **Tidak ada perbedaan antara kode dan dokumentasi.**
- Missing handling: mahasiswa non-LULUS (aktif/DO/undur diri) → target `NULL`. Label biner hanya untuk yang sudah lulus — disengaja untuk binary classification.

---

## 8. Time / Semester Logic

| Operasi | Formula | Waktu dipakai | Catatan |
|---|---|---|---|
| `lama_studi_bulan` (mahasiswa aktif) | `ceil(months_between(current_date(), tanggal_masuk))` | `tanggal_keluar` NULL | Menggunakan **hari ini** — nilai berubah seiring waktu; mau tidak mau runtime-dependent |
| `lama_studi_bulan` (sudah keluar) | `ceil(months_between(tanggal_keluar, tanggal_masuk))` | `tanggal_keluar` tersedia | Memakai tanggal keluar (informasi pasca-outcome) |
| `estimasi_semester` | `ceil(lama_studi_bulan / 6)` | — | Threshold 8 semester hardcoded |

- **Risiko konsep waktu:** untuk mahasiswa yang sudah lulus, `estimasi_semester` dihitung **setelah outcome** (dari tanggal keluar). Ketika feature ini dipakai sebagai predictor untuk data training (yang semuanya lulus → semua punya tanggal_keluar), nilai feature telah "menyerap" informasi akhir masa studi → sangat terkait dengan label.
- `months_between` sendiri mengabaikan hari sebagian (Spark menghitung fraksi) — implikasi kecil; hanya dapat diverifikasi dari data aktual → **NEEDS RUNTIME VERIFICATION**.

---

## 9. Student Eligibility

Filter di Gold `gold_mahasiswa.py`:
- **Tidak ada** `filter`, `where`, `dropna`, `dropDuplicates`, `distinct` pada data Gold di `gold_mahasiswa.py`. Semua mahasiswa dari Silver ikut ditulis ke gold (termasuk aktif, DO, dsb).
- Mahasiswa dengan `tanggal_masuk` NULL sudah disaring **sebelumnya di Silver** (`silver.py:85-87`, filter `tanggal_masuk IS NOT NULL` khusus `data_referensi_mahasiswa`).
- Fakta yang relevant: `tanggal_keluar` NULL baik-baik saja (aktif) → tetap ada di Gold.

**Filter mahasiswa jadi LULUS/AKTIF tidak terjadi di Gold, melainkan di Feature Store** (`training_dataset.py:40-42`, `inference_dataset.py:40-42`) — konsisten dengan keputusan bahwa Gold menyimpan semua siswa dan FS memilih sub-populasi.

---

## 10. Data Leakage Audit

Perhatian khusus karena Gold memproduksi **feature + label sekaligus**, dan feature ML dibangun dari **data final** mahasiswa yang sudah lulus.

| Feature | Source | Kapan informasi tersedia | Kenapa berpotensi leakage | Severity | Rekomendasi |
|---|---|---|---|---|---|
| `ipk` | Silver (nilai final) | Setelah studi selesai (untuk lulus) | IPK final sudah mengandung outcome; pada training semua sample lulus → feature mengetahui hasil akhir **sebelum** memprediksi ketepatan waktu | **POTENTIAL LEAKAGE — NEEDS DESIGN REVIEW** | Review apakah feature seharusnya dinilai pada titik waktu sebelum kelulusan (mis. IPK per-semester) |
| `total_sks` / `jumlah_mk` | Silver (nilai final) | Saat kelulusan | Sama: nilai total akhir setelah seluruh semester | **POTENTIAL LEAKAGE — NEEDS DESIGN REVIEW** | Sama |
| `persentase_sks` | `total_sks` final / konstanta kurikulum | Saat kelulusan | Derivatif dari total_sks final | **POTENTIAL LEAKAGE — NEEDS DESIGN REVIEW** | Ikut keputusan total_sks |
| `estimasi_semester` | `lama_studi_bulan` ← `tanggal_keluar` | Hanya setelah kelulusan untuk yang lulus (tanggal_keluar harus ada) | Feature dihitung dari **tanggal keluar** (outcome). Di training, semua mahasiswa LULUS → semua punya tanggal_keluar → feature sudah "melihat" panjang studi aktual. Label `status_kelulusan` juga diturunkan dari `estimasi_semester` (<=8 → Tepat Waktu). **Korelasi antara feature dan label bukan hanya kuat — struktural:** label = fungsi dari feature | **POTENTIAL LEAKAGE — HIGH, DILAPORKAN — NEEDS DESIGN REVIEW** | Definisi ulang adalah keputusan penelitian; dilarang diubah pada audit ini |
| `lama_studi_bulan` | `tanggal_keluar`/`current_date` | Pasca-outcome (lulus) | Intermediate; bisa dianggap leakage bila dipakai sebagai feature (tidak). | Informasi | Tidak dipakai di FS |
| `status_kelulusan` | label | outcome | Label saja, **tidak** masuk ke feature (verifikasi: `data_preparation.py` memisahkan `label` dari `features`; FS select memisahkan kolom label) | — | OK |

Poin penting (bukan asumsi, dari kode):
- Label `status_kelulusan` **tidak dipakai sebagai feature** — terpisah bersih di `training_dataset.py`/`data_preparation.py`. ✅
- Namun feature `estimasi_semester` berasal dari **tanggal_keluar (outcome)**, dan label adalah fungsi dari feature tersebut. Ini berarti pada training, model dapat "menebak" label hampir sempurna hanya dari `estimasi_semester` → **perlu keputusan penelitian** apakah desain ini diterima (mis. penelitian memang memprediksi klasifikasi ketepatan berdasarkan lama studi). **Tidak diubah.**

---

## 11. Null Handling

| Operasi | Lokasi | Efek |
|---|---|---|
| `when(tanggal_keluar.isNull(), ...)` | gold.py:82 | Mahasiswa aktif → lama studi pakai `current_date()`. Tidak menghapus baris. |
| `lit(None)` saat status != "LULUS" | gold.py:138 | Label NULL untuk non-lulus. Tidak menghapus baris. |
| Tidak ada `dropna`/`fillna`/`coalesce` di Gold | — | NULL feature (mis. `total_sks` NULL) **tetap lolos** ke Gold; baru dibuang di Feature Store (`dropna` pada kolom feature) |

Penilaian: **Gold tidak menghapus mahasiswa akibat NULL.** Baris NULL tetap ditulis; FS yang memfilter. Ini mencegah hilangnya record sebelum sempat didiagnosis. Konsisten dengan desain.

---

## 12. Duplicate / Key Validation

- Gold `gold_mahasiswa` **tidak** melakukan `dropDuplicates`/`distinct` — baris per mahasiswa mengikuti Silver (yang juga tidak dedup).
- **Tidak ada key eksplisit** (mis. NIM) yang dipertahankan/dipakai sebagai grain guard di Gold. Jika Silver `data_referensi_mahasiswa` berisi >1 baris per NIM, gold akan menyimpan >1 row per mahasiswa → **grain "1 mahasiswa = 1 row" tidak dijamin oleh Gold** → bergantung data sumber → **NEEDS RUNTIME VERIFICATION**.
- `gold_program_studi` & `gold_kurikulum` passthrough → grain mengikuti sumber.

---

## 13. Data Loss Analysis

| Operasi | Lokasi | Apa yang hilang | Disengaja? | Bukti statis | Perlu runtime? |
|---|---|---|---|---|---|
| Filter `tanggal_masuk IS NOT NULL` (di Silver) | `silver.py:85-87` | Mahasiswa tanpa tanggal masuk | Ya — cleansing Silver | Ya | Jumlah baris terdampak belum diketahui |
| Casting non-monotonik (`cast("int")`, `cast("double")`, `cast("date")`) | gold.py:39-46 | Nilai non-numerik/invalid menjadi NULL | Tidak langsung | Parsing bisa menghasilkan NULL bila nilai tidak cocok | **YA** — verifikasi apakah ada nilai yang menjadi NULL |
| `createOrReplace()` | gold.py:181, gold_prodi.py:28, gold_kurikulum.py:28 | Data Gold sebelumnya di-overwrite (tidak ada sejarah) | Ya — desain `createOrReplace` | Ya | Overwrite penuh tiap run |
| Constanta `jumlah_sks_kurikulum` = `.first()` | gold.py:56-60 | Bila kurikulum kosong → error / nilai NULL → `persentase_sks` NULL | Tidak | Tidak dapat dibuktikan | **YA** |

Tidak ada `inner join`, `dropDuplicates`, `distinct`, `drop`, atau aggregation yang mengganti count di Gold.

---

## 14. Gold → Feature Store Contract

| | Contract | Status |
|---|---|---|
| Tabel yang dibaca FS | `gold.gold_mahasiswa` (`training_dataset.py:22`, `inference_dataset.py:22`) | ✅ sesuai nama |
| Feature yang dipakai FS/ML | `jenis_kelamin`, `estimasi_semester`, `ipk`, `total_sks`, `jumlah_mk`, `persentase_sks` | ✅ semua ada di Gold |
| Label yang dipakai FS/ML | `status_kelulusan` | ✅ ada di Gold |
| Kolom filter FS | `status_mahasiswa` (LULUS/AKTIF) | ✅ ada di Gold (di-trim) |
| Dropna FS | kolom feature + label | ✅ sesuai |
| Grain FS | 1 row = 1 mahasiswa (dari gold) | mengikuti Gold (lihat §12) |
| Catalog/namespace | `iceberg.gold.gold_mahasiswa` | ✅ konsisten Phase 2 |

**Verdict:** **tidak ada `GOLD → FEATURE STORE CONTRACT ISSUE`** ditemukan. Nama kolom, grain, label, dan catalog cocok antara Gold dan Feature Store.

---

## 15. Performance Findings

- `df.count()` dipanggil **7×** di `gold_mahasiswa.py` (setiap tahap dikus jumlah) + `first()` + `groupBy(...).count().show()` 2× → banyak aksi Spark (job) pada dataset tunggal. Berat di mode cluster tetapi bukan bug; hanya efisiensi.
- `jumlah_sks_kurikulum` diambil via `.first()` (aksi) sebelum transformasi utama.
- Tidak ada `collect()`, `toPandas()`, `crossJoin`, window/`orderBy` di Gold.
- SparkSession dibuat per fungsi Gold (3×) melalui `get_spark` — sama dengan pola Phase 4 (session churn). Catatan bukan perubahan.

---

## 16. Findings

### Critical
- Tidak ada.

### High
- **POTENTIAL DATA LEAKAGE — `estimasi_semester` sebagai feature yang diturunkan dari `tanggal_keluar` (outcome), sedangkan label `status_kelulusan` juga merupakan fungsi dari `estimasi_semester`.** Pada populasi training (semua LULUS), feature dan label berkorelasi struktural. Ini adalah **keputusan penelitian** dan tidak diubah pada audit. (Rinci di §10.)

### Medium
- **Netralisasi definisi feature menggunakan data final (pasca-lulus):** `ipk`, `total_sks`, `jumlah_mk`, `persentase_sks`, `estimasi_semester` semuanya dihitung dari nilai akhir studi → berpotensi leakage terhadap label. Masing-masing → **NEEDS DESIGN REVIEW** (keputusan peneliti).
- **Kurikulum single-row assumption:** `jumlah_sks_kurikulum = kurikulum.select(...).first()[0]` memakai baris pertama saja; bila banyak kurikulum atau tabel kosong → konstanta salah / error/NULL. **NEEDS RUNTIME VERIFICATION**.
- **Grain "1 mahasiswa = 1 row" tidak dijaga di Gold** (tanpa dedup/key guard) → bergantung data sumber. **NEEDS RUNTIME VERIFICATION**.

### Low
- Multiple `count()` / `.first()` actions → efisiensi (bukan correctness).
- Threshold `estimasi_semester <= 8` dan `/6` hardcoded tanpa konstanta/dokumentasi kebijakan akademik.
- `gold_program_studi` & `gold_kurikulum` benar-benar passthrough — tidak ada agregasi/transformasi bisnis (sejalan REVIEW_PROJECT §5.6).

### Potential Data Leakage
1. `estimasi_semester` ← `tanggal_keluar` (outcome) — High, NEEDS DESIGN REVIEW.
2. `ipk`, `total_sks`, `jumlah_mk`, `persentase_sks` final (post-outcome) — Medium, NEEDS DESIGN REVIEW.
3. TIDAK: label tidak masuk ke feature; feature tidak bisa melihat label (verified di FS/ML).

### Gold → Feature Store Contract Issue
- **Tidak ada.** Contract lengkap dan cocok (see §14).

### Needs Runtime Verification
1. Jumlah baris Gold vs Silver per tabel (`count` aktual, apakah ada mahasiswa hilang).
2. Apakah `cast` menyebabkan NULL baru (nilai non-numerik/invalid pada IPK/SKS/MK/tanggal).
3. Apakah dataset kurikulum memiliki tepat satu baris & nilai `jumlah_sks_total` non-NULL.
4. Apakah `data_referensi_mahasiswa` memang unik per NIM (grain 1:1).
5. Nilai `estimasi_semester` aktual → verifikasi distribusi vs label (leakage kuantitatif).
6. Format tanggal aktual apakah bisa di-`cast("date")` tanpa NULL.

### Needs Design Review
1. Definisi feature berbasis data final vs titik-waktu-per-semester (leakage).
2. Penggunaan `estimasi_semester` sebagai feature padahal label = f(estimasi_semester).
3. Kebijakan konstanta `jumlah_sks_kurikulum` bila >1 kurikulum per prodi.
4. Threshold 8 semester / pembulatan 6 bulan per semester.
5. Apakah Gold perlu menjaga grain key (mis. NIM) bila dedup diperlukan.

---

## 17. Changes Made

| File | Masalah | Perubahan | Alasan |
|---|---|---|---|
| *(tidak ada file kode diubah)* | — | — | Tidak ditemukan bug yang dapat dibuktikan statis di Gold. Semua temuan adalah **keputusan penelitian/desain** (feature final, konstanta kurikulum, grain, threshold) yang dilarang diubah pada tahap ini, atau memerlukan data aktual/runtime. Sesuai aturan: **jika ragu, jangan ubah**. |

Dokumen ini (`docs/CODE_AUDIT_PHASE_05_GOLD.md`) adalah output audit.

---

## 18. Files Reviewed But Not Changed

- `backend/gold/gold_mahasiswa.py`, `backend/gold/gold_prodi.py`, `backend/gold/gold_kurikulum.py`, `backend/gold/gold.py`
- `backend/feature_store/feature_store.py`, `backend/feature_store/training_dataset.py`, `backend/feature_store/inference_dataset.py` (contract saja)
- `backend/ml/train.py`, `backend/ml/data_preparation.py` (kontrak kolom label/feature)
- `backend/serving/postgres_sink.py` (kontrak: menerima `gold_mahasiswa`, `gold_program_studi`, `gold_kurikulum`)
- `backend/services/prediction_service.py`, `backend/services/batch_prediction_service.py` (feature set)
- `backend/silver/silver.py`, `backend/bronze/bronze.py`, `backend/spark/session.py`, `backend/config/settings.py`
- `scripts/test_gold.py`, `scripts/check_gold.py`, `scripts/cek_count.py`, `scripts/cek_data.py`, `scripts/check_feature_store.py`, `docker/superset/trino_config.py`
- Docs: `docs/ALUR_PENGERJAAN.md`, `docs/REVIEW_PROJECT.md`, `docs/CODE_AUDIT_PHASE_03_BRONZE.md`, `docs/CODE_AUDIT_PHASE_04_SILVER.md`

---

## 19. Runtime Verification Checklist

> Tidak ada item yang dicentang; verifikasi dilakukan nanti di komputer lab (Docker menyala).

- [ ] Semua Gold table berhasil dibuat
- [ ] Grain Gold sesuai desain
- [ ] Join tidak menyebabkan row multiplication
- [ ] Tidak ada mahasiswa hilang secara tidak disengaja
- [ ] Aggregation menghasilkan jumlah yang benar
- [ ] Feature engineering menghasilkan nilai yang benar
- [ ] Target menghasilkan kelas yang benar
- [ ] Tidak ada data leakage
- [ ] Datatype sesuai
- [ ] Gold dapat dibaca kembali
- [ ] Gold tersimpan di MinIO
- [ ] Gold → Feature Store contract sesuai