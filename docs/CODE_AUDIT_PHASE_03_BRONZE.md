# Phase 3 — Bronze Layer Audit

Audit statis (tanpa menjalankan aplikasi/service) pada **Bronze Layer** project Tugas Akhir:

> **"Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis Machine Learning"**

Project utama: `D:\TugasAkhirNita\`

Acuan arsitektur: **Docker-based** (Spark berjalan di dalam Docker; komunikasi antar-container memakai service name; Iceberg + MinIO).

---

## 1. Scope

Audit dibatasi pada:

- `backend/bronze/bronze.py` (inti Bronze)
- File yang dipanggil Bronze: `backend/spark/session.py`, `backend/config/settings.py`, `backend/utils/logger.py`
- Utils yang terkait input file: `backend/utils/file_utils.py`, `backend/utils/excel_utils.py`
- Script yang secara langsung membuat/memeriksa Bronze: `scripts/test_bronze.py`
- Konfigurasi Iceberg/MinIO (Tahap 2) sebagai acuan
- Referensi ke Silver/Gold **hanya** untuk memahami output Bronze (tidak diubah)

Tahapan setelah Bronze (**Silver, Gold, Feature Store, ML, Airflow, Trino, Superset**) tidak diaudit.

---

## 2. Bronze Architecture

```text
Data Akademik (data/req_data_rut.xlsx — Excel multi-sheet)
        ↓  (path diteruskan dari FastAPI / pipeline service)
Spark di Docker (backend/spark/session.py — catalog Iceberg)
        ↓  spark.read.format("com.crealytics.spark.excel") per sheet
Bronze Layer (backend/bronze/bronze.py)
        ↓  df.writeTo("iceberg.bronze.<table>").using("iceberg").createOrReplace()
Apache Iceberg (catalog 'iceberg' = Hive Metastore)
        ↓
MinIO (s3a://warehouse/iceberg/bronze/...)
```

Session Spark tunggal (`get_spark("Bronze Layer")`) dipakai untuk seluruh sheet; tidak ada SparkSession kedua di Bronze.

---

## 3. Input Data

Berdasarkan kode & dokumentasi project:

| Aspek | Nilai | Sumber |
|---|---|---|
| File | `data/req_data_rut.xlsx` | `scripts/test_bronze.py`, `docs/ALUR_PENGERJAAN.md`, `backend/api/upload.py` |
| Format | Excel `.xlsx` (`.xls` juga diterima API upload) | `backend/api/upload.py` |
| Pembacaan sheet | enumerasi ulang seluruh `sheet_names` dari `pandas.ExcelFile(file_path)` | `backend/bronze/bronze.py:36-43` |
| Daftar sheet (ekspektasi) | `Data Referensi Mahasiswa`, `Data KHS`, `Data Program Studi`, `Data Kurikulum` | `docs/ALUR_PENGERJAAN.md`, `docs/REVIEW_PROJECT.md`, `backend/services/batch_prediction_service.py:26-27` |

> **Catatan:** Bronze membaca **semua sheet** secara dinamis (loop `excel.sheet_names`), bukan daftar hardcoded. Nama tabel diturunkan dari nama sheet.

---

## 4. Bronze Processing

Urutan pemrosesan per sheet (`backend/bronze/bronze.py`):

1. **Preflight pandas** (`pd.read_excel(file_path, sheet_name=sheet)`):
   - Gagal dibaca → `logger.warning` + masuk `skipped_sheets` (sheet dilewati).
   - `preview.empty` (sheet kosong) → dilewati.
   - `len(preview.columns) == 0` (tidak ada kolom) → dilewati.
2. **Baca dengan Spark**:
   - `spark.read.format("com.crealytics.spark.excel")`
   - `.option("header", "true")`
   - `.option("inferSchema", "true")`
   - `.option("dataAddress", f"'{sheet}'!A1")`
   - `.load(str(file_path))`
3. **Penamaan tabel**: `excel_sheet_to_table(sheet)` — `strip().lower()`, spasi/`-`/`/` → `_`, tanda kurung dibuang.
4. **Tulis Iceberg**: `df.writeTo("iceberg.bronze.<table>").using("iceberg").createOrReplace()`.

### 4.1 Reading
- Dua tahap pembacaan: pandas (validasi) + Spark (data). Kosong kolom/baris divalidasi via pandas.
- Header diambil dari baris 1 (`header=true`), data mulai A1.

### 4.2 Normalization
- **Kolom**: TIDAK dinormalisasi di Bronze — header asli dipertahankan (mis. `Status Mahasiswa` tetap dengan spasi). Normalisasi kolom adalah tanggung jawab Silver (`clean_column_name`). Ini sesuai prinsip Bronze (menyimpan sedekat mungkin dengan sumber).
- **Tabel**: nama hasil `excel_sheet_to_table` (lowercase, separator `_`).

### 4.3 Datatype
- `inferSchema=true` pada spark-excel: tipe di-infer otomatis (long, double, string, date). Tidak ada konversi eksplisit dan tidak ada transformasi bisnis. Risiko inferensi tipe dicatat di §8/§9.

### 4.4 Transformation
- Hanya transformasi teknis minimal (penamaan tabel). Tidak ada feature engineering, tidak ada join antar-sheet, tidak ada agregasi.

### 4.5 Filtering
- Tidak ada `filter`/`where`/`dropna`/`drop_duplicates` pada data Bronze.
- Satu-satunya "penyaringan" adalah **skip whole-sheet** pada preflight (sheet gagal/kosong/tanpa kolom) — baris di dalam sheet yang lolos tidak disaring.

### 4.6 Duplicate handling
- **Tidak menghapus duplicate.** Semua baris dari sheet dipertahankan apa adanya. Ini konsisten untuk layer awal data lakehouse (menyimpan catatan penuh).

---

## 5. Bronze Tables

| Source / Sheet | Bronze Table | Catalog | Namespace | Format |
|---|---|---|---|---|
| `Data Referensi Mahasiswa` | `data_referensi_mahasiswa` | `iceberg` | `bronze` | Iceberg |
| `Data KHS` | `data_khs` | `iceberg` | `bronze` | Iceberg |
| `Data Program Studi` | `data_program_studi` | `iceberg` | `bronze` | Iceberg |
| `Data Kurikulum` | `data_kurikulum` | `iceberg` | `bronze` | Iceberg |

*(Daftar sheet diambil dari dokumentasi project; karena sifatnya dinamis, tabel yang benar-benar dibuat = seluruh sheet non-kosong yang ada di workbook.)*

Referensi penulisan: `f"{ICEBERG_NAMESPACE}.bronze.{table_name}"` — dengan `ICEBERG_NAMESPACE = ICEBERG_CATALOG = "iceberg"` (mode cluster, Tahap 2). Tidak ada `local.` / `lakehouse.` literal di Bronze.

---

## 6. Storage Configuration

- Catalog Iceberg: `iceberg` (tipe `hive`, HMS `thrift://hive-metastore:9083`, warehouse `s3a://warehouse/iceberg`) — dari `backend/config/settings.py` dan `backend/spark/session.py:_iceberg_configs`.
- S3A: `fs.s3a.endpoint=http://minio:9000` (service name), path-style access, credentials dari environment — konsisten dengan Tahap 2.
- Nama namespace `bronze` dibuat otomatis oleh `get_spark` (`CREATE NAMESPACE IF NOT EXISTS iceberg.bronze`).
- Untuk `.xlsx` read, Spark memakai jar `com.crealytics:spark-excel_2.12:3.5.1_0.20.4` (terdaftar di `spark.jars.packages` pada `session.py`). Python `openpyxl==3.1.5` tersedia untuk preflight pandas.

---

## 7. Path Configuration

| Path | Lokasi | Pemakaian | Portabilitas |
|---|---|---|---|
| `DATA_DIR` (`PROJECT_ROOT/data`) | `backend/config/settings.py` | input upload & pipeline (anchor absolut PROJECT_ROOT) | Aman |
| `Path("data/req_data_rut.xlsx")` (lama) | `scripts/test_bronze.py` | input bronze (relatif CWD) | **Diperbaiki → `DATA_DIR`** (lihat §10) |
| `str(file_path)` diteruskan ke Spark | `backend/bronze/bronze.py:102` | input file yang dibaca Spark | **NEEDS RUNTIME VERIFICATION** (diskusi di bawah) |
| `s3a://warehouse/iceberg` | Iceberg warehouse | output tabel Bronze | Aman (MinIO service) |

> Tidak ada hardcode `D:\`, `C:\`, `/mnt/d/` di kode Bronze.

**Isu portabilitas penting (container):**
File input `.xlsx` berada di host (`data/`) dan path-nya diteruskan mentah ke `spark.read...load(str(file_path))`. Dalam arsitektur yang ditargetkan (Spark berjalan penuh di Docker / profile `spark-docker`), executor/worker container tidak men-mount `./data` (cek `docker-compose.yml`: service `spark-master`/`spark-worker` hanya men-mount volume `spark-logs`), sehingga path host tidak otomatis terlihat dari container.

- Bila driver+executors berjalan di **host Windows** (mode client ke `spark://spark-master:7077`), path host dapat terbaca tapi **executors di container** tetap perlu akses file → berisiko `FileNotFoundError` di sisi executor.
- Bila seluruh Spark berjalan **di dalam container**, path host harus di-mount ke container (perubahan Compose) atau file harus dibaca dari **MinIO `raw`** (bucket `raw` sudah di-seed `req_data_rut.xlsx` oleh `docker/minio/init.sh`).

→ Tidak diubah di fase ini karena merupakan **keputusan desain** (sumber input Bronze: host path vs MinIO raw). Dicatat di §9.

---

## 8. Data Loss Risk

| Operasi | Lokasi | Penilaian |
|---|---|---|
| `preview.empty` → skip sheet | `bronze.py:72` | Aman: hanya sheet kosong. Baris dalam sheet yang terbaca tidak dibuang. |
| `len(preview.columns)==0` → skip sheet | `bronze.py:84` | Aman: sheet tanpa kolom tidak punya data berarti. |
| `try/except` baca sheet gagal → skip | `bronze.py:52-66` | **Perhatian:** sheet yang gagal dibaca oleh **pandas** di-skip walau Spark mungkin bisa membacanya (mis. `.xls` tanpa engine xlrd). Berpotensi tabel tidak dibuat untuk sheet yang sebenarnya valid. |
| `inferSchema=true` | `bronze.py:100` | **Risiko:** kolom alfanumerik yang tampak numerik (contoh NIM/kode dengan leading zero) bisa di-infer `long`/`double` → kehilangan leading zero/format asli. Juga risiko presisi untuk angka panjang. Perlu verifikasi schema aktual. |
| `createOrReplace()` | `bronze.py:116` | Replace-if-exists (bukan append). Menjalankan run kedua dengan file yang sama → tabel di-replace dengan data identik (tidak ada duplikasi). Jika file berubah, data lama tergantikan. Konsisten dengan Bronze sebagai snapshot terbaru. |
| `df.count()` sebelum tulis | `bronze.py:108` | Tidak menghapus data (hanya aksi Spark untuk log). |
| Skip sheet → tabel lama tetap ada | — | Jika sheet sebelumnya ada lalu pada run berikutnya di-skip, `createOrReplace` tidak menyentuh tabel → **stale table tertinggal**. Dicatat, bukan bug fatal. |

Penghapusan data: **tidak ada** `dropna`, `drop_duplicates`, `filter`, `where`, `drop`, `fillna` pada data Bronze.

---

## 9. Findings

### Critical
- Tidak ada temuan Critical yang dapat dibuktikan statis.

### High
- Tidak ada temuan High yang dapat dibuktikan murni statis.

### Medium
1. **Sumber input Bronze dari path host yang tidak di-mount ke container Spark** (`bronze.py:102` `spark.read...load(str(file_path))`). Kompon file `data/` tidak di-mount ke `spark-worker`; pada arsitektur Docker-based, berpotensi `FileNotFoundError` di executor. Opsi: mount volume atau baca dari MinIO `raw` (bucket sudah di-seed). **Tidak diubah** karena menyangkut desain pipeline (lihat arsitektur Tahap 2).
2. **`inferSchema=true` berpotensi merusak tipe asli** (leading zero di kode/NIM, presisi). Bronze seharusnya menyimpan sedekat mungkin ke sumber. Tidak diubah tanpa schema eksplisit dari dataset aktual (perlu runtime untuk melihat tipe infer).

### Low
3. **Preflight pandas vs Spark read bisa tidak sinkron** pada format `.xls`: pandas butuh engine `xlrd` (tidak ada di `requirements.txt`), sementara Spark/poi bisa membaca `.xls`. Akibat: sheet di-skip oleh preflight padahal tersimpan data. Scrib sheet yang valid pada `.xlsx` (default) tidak terpengaruh.
4. **Stale table bila sheet di-skip pada run berikutnya** — tabel Bronze yang tidak lagi ditulis `createOrReplace` tetap bertahan di catalog.
5. `docs/ALUR_PENGERJAAN.md` & plan `2026-08-03-lightweight-local-spark` masih mendokumentasikan mode Spark lokal (superseded oleh keputusan Docker-based) — dokumentasi, bukan kode Bronze.

### Needs Runtime Verification
1. `spark.read...load(str(file_path))` terhadap path host ketika Spark berjalan di Docker (apakah file terlihat dari driver/executors).
2. Schema hasil `inferSchema=true` untuk setiap sheet (apakah tanggal/NIM/IPK/SKS ter-infer benar dan tidak kehilangan leading zero).
3. `dataAddress="'{sheet}'!A1"` valid untuk nama sheet ber-spasi (`Data Referensi Mahasiswa` dst.).
4. Apakah tabel `iceberg.bronze.*` terbaca kembali oleh `show`/select setelah `createOrReplace`.

### Needs Design Review
1. Sumber input Bronze: path host (`data/`) vs MinIO `raw` bucket — agar konsisten dengan data lake & Spark-Docker.
2. Kebijakan overwrite: `createOrReplace()` (snapshot terbaru) vs `append` — keputusan proyek, tidak diubah.
3. Apakah `.xls` tetap didukung (perlu `xlrd` atau batasi ke `.xlsx`).

---

## 10. Changes Made

| File | Masalah | Perubahan | Alasan |
|---|---|---|---|
| `scripts/test_bronze.py` | `Path("data/req_data_rut.xlsx")` — path relatif terhadap CWD (rentan bila dipanggil dari direktori lain) | Ganti ke `DATA_DIR / "req_data_rut.xlsx"` (import `from backend.config.settings import DATA_DIR`) | Konsisten dengan perbaikan Phase 1 (`upload.py`, `prediction_service.py`, `batch_prediction_service.py`) dan `settings.PROJECT_ROOT`-anchored; tidak mengubah sumber data maupun perilaku Bronze. |

Tidak ada perubahan pada `backend/bronze/bronze.py` — tidak ditemukan bug/inkonsistensi yang aman dibuktikan statis (semua temuan berpotensi mengubah desain atau butuh runtime untuk dikonfirmasi).

---

## 11. Files Reviewed But Not Changed

- `backend/config/settings.py` — default Docker (S3 endpoint `minio:9000`, HMS `hive-metastore:9083`, catalog `iceberg`, warehouse `s3a://warehouse/iceberg`)
- `backend/spark/session.py` — single session, `spark.sql.extensions` Iceberg, jar spark-excel tersedia, namespace dibuat otomatis
- `backend/utils/logger.py`, `backend/utils/file_utils.py`, `backend/utils/excel_utils.py`
- `docker-compose.yml` (mayornya acuan: service name `minio`, `hive-metastore`, `spark-master/worker`)
- `docker/minio/init.sh` (seed bucket `raw`)
- `scripts/cek_count.py` (membaca `iceberg.bronze.data_referensi_mahasiswa`)
- `backend/services/pipeline_service.py`, `backend/api/upload.py`, `backend/api/pipeline.py` (pemanggil Bronze — hanya ditelusuri untuk memahami input)
- `backend/silver/silver.py` (hanya untuk memahami konsumen output Bronze; tidak diubah)
- `docs/ALUR_PENGERJAAN.md`, `docs/REVIEW_PROJECT.md` (dokumentasi alur/dataset)

---

## 12. Runtime Verification Checklist

> Tidak ada item yang dicentang; verifikasi dilakukan nanti di komputer lab (Docker menyala).

- [ ] Input file dapat dibaca
- [ ] Seluruh sheet yang diperlukan terbaca
- [ ] Spark dapat membaca input
- [ ] Bronze table berhasil dibuat
- [ ] Bronze table tersimpan sebagai Iceberg
- [ ] Iceberg table dapat dibaca kembali
- [ ] Data tersimpan di MinIO
- [ ] Schema Bronze sesuai
- [ ] Tidak ada data yang hilang secara tidak disengaja
- [ ] Pipeline dapat dijalankan ulang sesuai behavior yang dirancang