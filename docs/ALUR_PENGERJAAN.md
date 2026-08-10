# Alur Pengerjaan Project — Prediksi Tingkat Kelulusan Mahasiswa ITERA

> **Judul TA:** Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa di ITERA Berbasis Machine Learning
>
> Dokumen ini mencatat alur pengerjaan project dari awal sampai akhir, dengan penekanan pada detail proses pengolahan data.

---

## 1. Gambaran Umum Arsitektur

Project membangun **data lakehouse** dengan pipeline ETL berlapis menggunakan **Apache Spark + Apache Iceberg**, kemudian mengintegrasikan **Gold Layer** ke **Feature Store** untuk melatih model prediksi kelulusan mahasiswa (Gaussian Naive Bayes).

```text
Raw Excel (data/req_data_rut.xlsx)
        |
        v
  [Bronze Layer]   -> ingest mentah per-sheet ke Iceberg (bronze.*)
        |
        v
  [Silver Layer]   -> pembersihan & standardisasi (silver.*)
        |
        v
  [Gold Layer]     -> agregasi domain & feature engineering (gold.*)
        |
        +------------------------------+---------------------------+
        v                              v                           v
 [Feature Store]              [PostgreSQL Serving]          [Trino -> Superset]
 training_dataset            publish_gold_tables()        query analitik dashboard
 inference_dataset           (gold_mahasiswa, dll)
        |
        v
 [ML Pipeline] -> prepared dataset -> train/test 80:20
        |                -> Gaussian Naive Bayes (CrossValidator 10-fold)
        v
 [Model Registry] -> models/gaussian_nb + models/metadata.txt
        |
        v
 [Prediction] -> inference_dataset -> probabilitas prediksi kelulusan
```

### Komponen Teknologi

| Komponen | Peran | Mode |
|---|---|---|
| Apache Spark 3.5.3 | Engine ETL & ML | **lokal** (`local[*]`, di mesin Windows) atau cluster Docker opsional |
| Apache Iceberg | Format tabel lakehouse (bronze/silver/gold/feature_store) | Catalog `iceberg` (Hive Metastore) |
| MinIO | Object storage / data lake (S3-compatible) | Docker |
| Hive Metastore | Metadata Iceberg | Docker |
| Trino | SQL engine untuk Superset | Docker |
| Apache Superset | Dashboard BI | Docker |
| Apache Airflow | Orkestrasi pipeline harian | Docker |
| PostgreSQL 16 | Serving layer + metadata Airflow/Superset/HMS | Docker |
| FastAPI | Backend API (upload, pipeline, train, predict) | Host Windows |

---

## 2. Persiapan Environment

### 2.1 Kebutuhan

- Docker Desktop + Docker Compose.
- Python 3.11 + dependency `requirements.txt`.
- JDK sesuai PySpark (untuk pipeline Spark di host Windows).
- RAM laptop terbatas (±5,9 GB) → strategi: **Spark lokal**, service lakehouse di Docker.

### 2.2 Setup

```powershell
Copy-Item .env.example .env   # salin template credential
```

Konfigurasi kunci `.env` (mode integrasi lokal):

```env
SPARK_MODE=local
SPARK_MASTER_URL=local[*]
ICEBERG_CATALOG=iceberg
ICEBERG_WAREHOUSE=s3a://warehouse/iceberg
S3_ENDPOINT=http://localhost:9000
HIVE_METASTORE_URI=thrift://localhost:9083
POSTGRES_PORT=5432        # serving Superset/FastAPI
POSTGRES_HIVE_PORT=5433   # metadata Hive Metastore
POSTGRES_AIRFLOW_PORT=5434 # metadata Airflow
```

Catatan penting:

- `ICEBERG_CATALOG=iceberg` memakai **Hive Metastore** + warehouse di **MinIO** (mode integrasi dengan Docker).
- Alternatif `ICEBERG_CATALOG=local` → warehouse folder lokal `iceberg/` tanpa Docker (mode sandbox).
- Versi dependency diselaraskan ke **Spark 3.5**: `pyspark==3.5.3`, `py4j==0.10.9.7`.
- `backend/spark/session.py` men-download otomatis: `iceberg-spark-runtime-3.5_2.12:1.5.2`, `spark-excel_2.12:3.5.1_0.20.4`, `postgresql:42.7.4`, `hadoop-aws:3.3.4`, `aws-java-sdk-bundle`.

### 2.3 Startup Docker

```powershell
docker compose up -d --build        # service default (tanpa Spark & superset-worker)
docker compose config --quiet       # validasi sintaks compose
```

- Spark master/worker/history diaktifkan opsional: `docker compose --profile spark-docker up -d`.
- `superset-worker` opsional: `docker compose --profile superset-worker up -d`.
- Batas memori diterapkan: trino `3g`, superset `2g`, hive-metastore `2g`, airflow scheduler & webserver `1g`.

---

## 3. Sumber Data Mentah

File: **`data/req_data_rut.xlsx`** — satu file Excel multi-sheet:

| Sheet | Perkiraan baris | Isi |
|---|---|---|
| Referensi | 37.681 | Data mahasiswa (NIM, prodi, jalur masuk, status, tanggal masuk/keluar, IPK, SKS, dst.) |
| KHS | 22.029 | Kartu Hasil Studi (mata kuliah) |
| Prodi | 44 | Daftar program studi |
| Kurikulum | 147 | Struktur kurikulum + jumlah SKS total |

> **Keputusan penting:** skema matching/linkage antar sheet (mis. KHS ↔ Referensi) **dibatalkan** karena tidak ada kunci penghubung yang bersih. Pipeline berjalan murni: **Raw Excel → Bronze → Silver → Gold → Feature Store → ML → Prediksi**.

---

## 4. Pipeline Pengolahan Data

Semua tahap diorkestrasi oleh `backend/services/pipeline_service.py`:

```python
load_all_sheets_to_bronze(file_path)      # Bronze
process_all_tables()                      # Silver
process_gold()                            # Gold
publish_gold_tables(get_spark(...))       # PostgreSQL serving (Superset)
run_feature_store()                       # Feature Store
```

Dipicu dari 3 tempat: endpoint FastAPI `POST /upload/`, `POST /pipeline/run`, dan DAG Airflow (`docker/airflow/dags/prediction_pipeline.py`) melalui `http://host.docker.internal:8000/pipeline/run`.

### 4.1 Bronze Layer — `backend/bronze/bronze.py`

**Tujuan:** ingest mentah (raw) seluruh sheet Excel ke tabel Iceberg tanpa transformasi berarti.

1. Buka workbook dengan `pandas.ExcelFile` → daftar `sheet_names`.
2. Untuk setiap sheet:
   - **Preflight dengan pandas** (`pd.read_excel`):
     - Gagal dibaca → dicatat sebagai *skip*.
     - Kosong (`preview.empty`) → *skip*.
     - Tidak punya kolom → *skip*.
   - **Baca dengan Spark** (`com.crealytics.spark.excel`):
     - `header=true`, `inferSchema=true`, `dataAddress='<sheet>'!A1`.
   - **Penamaan tabel** (`excel_sheet_to_table`): nama sheet di-`lower()`, spasi/`-`/`/` diganti `_`, tanda kurung dibuang → `bronze.<nama>`.
   - Tulis: `df.writeTo("...bronze.<nama>").using("iceberg").createOrReplace()`.
3. Log ringkasan: tabel berhasil vs sheet yang di-skip.

Hasil: tabel di namespace `iceberg.bronze.*` (mis. `bronze.data_referensi_mahasiswa`, `bronze.data_khs`, `bronze.data_program_studi`, `bronze.data_kurikulum`).

### 4.2 Silver Layer — `backend/silver/silver.py`

**Tujuan:** membersihkan dan menstandardisasi data Bronze.

Untuk tiap tabel di `bronze` (`SHOW TABLES IN ...bronze`):

1. **Rename kolom konsisten** (`clean_column_name`):
   - `strip().lower()`, spasi/`-`/`/` → `_`, buang `(`, `)`, lalu `re.sub(r"[^a-zA-Z0-9_]", "", ...)`.
   - Contoh: `Status Mahasiswa` → `status_mahasiswa`.
2. **Trim semua kolom bertipe string** (`trim(col)`).
3. **Hapus baris kosong total** (`df.na.drop(how="all")`).
4. **Validasi khusus** untuk `data_referensi_mahasiswa`:
   - Hapus baris tanpa `tanggal_masuk` (`isNotNull`).
5. Simpan → `iceberg.silver.<nama>`.

Hasil: namespace `iceberg.silver.*` dengan kolom bersih, bebas spasi berlebih, tanpa baris semua-kosong.

### 4.3 Gold Layer — `backend/gold/*`

**Tujuan:** membangun tabel domain siap-analisis + feature engineering kelulusan.

#### 4.3.1 `gold_mahasiswa.py` (inti feature engineering)

Input: `silver.data_referensi_mahasiswa`.

1. **Konversi tipe data:**
   - `ipk` → `double`
   - `total_sks`, `jumlah_mk` → `int`
   - `tanggal_masuk`, `tanggal_keluar` → `date`
2. **Ambil konstanta kurikulum:** `jumlah_sks_total` dari `silver.data_kurikulum` (dipakai untuk persentase SKS).
3. **Normalisasi status:** `trim(status_mahasiswa)`.
4. **Feature `lama_studi_bulan`** (bulan):
   - Jika `tanggal_keluar` NULL (mahasiswa aktif): `ceil(months_between(current_date(), tanggal_masuk))`.
   - Jika sudah keluar: `ceil(months_between(tanggal_keluar, tanggal_masuk))`.
5. **Feature `estimasi_semester`:** `ceil(lama_studi_bulan / 6)`.
6. **Feature `persentase_sks`:** `(total_sks / jumlah_sks_kurikulum) * 100`.
7. **Feature `status_kelulusan`** (label):
   - Status mahasiswa `LULUS` + `estimasi_semester <= 8` → `"Tepat Waktu"`.
   - Status `LULUS` + `estimasi_semester > 8` → `"Terlambat"`.
   - Selain itu → `NULL`.
8. **Statistik diagnostik** (log): distribusi status mahasiswa, distribusi status kelulusan, jumlah lulus/aktif, jumlah NULL estimasi semester.
9. Simpan → `iceberg.gold.gold_mahasiswa`.

#### 4.3.2 `gold_prodi.py` & `gold_kurikulum.py`

- Baca `silver.data_program_studi` → simpan `gold.gold_program_studi`.
- Baca `silver.data_kurikulum` → simpan `gold.gold_kurikulum`.
- Keduanya tanpa transformasi tambahan (silver sudah bersih).

#### 4.3.3 `gold.py`

Orkestrator: jalankan `process_gold_mahasiswa()` → `process_gold_program_studi()` → `process_gold_kurikulum()`.

### 4.4 Serving ke PostgreSQL — `backend/serving/postgres_sink.py`

Setelah Gold dibuat, pipeline menyalin tabel Gold ke **PostgreSQL serving** (`academic_serving` di `localhost:5432`) agar kompatibel dengan alur lama dan query langsung:

- `gold_mahasiswa` → `public.gold_mahasiswa`
- `gold_program_studi` → `public.gold_program_studi`
- `gold_kurikulum` → `public.gold_kurikulum`

Teknik: `dataframe.write.jdbc(..., mode="overwrite")` dengan driver `org.postgresql.Driver`. Iceberg tetap menjadi **source of truth**; Superset membaca lewat Trino, bukan PostgreSQL ini.

### 4.5 Feature Store — `backend/feature_store/*`

**Tujuan:** menyiapkan dataset latih (label) dan dataset inferensi (tanpa label) dari Gold Mahasiswa.

#### `training_dataset.py` — `feature_store.training_dataset`

1. Baca `gold.gold_mahasiswa`.
2. **Filter hanya mahasiswa `LULUS`** (populasi yang labelnya diketahui).
3. **Drop baris NULL** pada kolom: `jenis_kelamin`, `estimasi_semester`, `ipk`, `total_sks`, `jumlah_mk`, `persentase_sks`, `status_kelulusan`.
4. **Pilih fitur + label:**
   - Fitur: `jenis_kelamin`, `estimasi_semester`, `ipk`, `total_sks`, `jumlah_mk`, `persentase_sks` (6 fitur).
   - Label: `status_kelulusan` (`"Tepat Waktu"` / `"Terlambat"`).
5. Simpan → `iceberg.feature_store.training_dataset`.

#### `inference_dataset.py` — `feature_store.inference_dataset`

1. Baca `gold.gold_mahasiswa`.
2. **Filter hanya mahasiswa `AKTIF`** (yang akan diprediksi).
3. Drop baris NULL pada fitur yang sama (tanpa label).
4. Pilih 6 fitur yang identik dengan training.
5. Simpan → `iceberg.feature_store.inference_dataset`.

#### `feature_store.py`

Orkestrator: buat training dataset lalu inference dataset.

---

## 5. Machine Learning — `backend/ml/*`

### 5.1 Persiapan Data — `data_preparation.py`

- Baca `feature_store.training_dataset`.
- **`StringIndexer`**:
  - `jenis_kelamin` → `jenis_kelamin_index`.
  - `status_kelulusan` → `label` (`handleInvalid="keep"`).
- **`VectorAssembler`** → kolom `features` dari `[jenis_kelamin_index, estimasi_semester, ipk, total_sks, jumlah_mk, persentase_sks]`.
- Gabung dalam **`Pipeline`** → hasil `prepared_df` dengan kolom `features` + `label`.

### 5.2 Training — `train.py`

- Split `prepared_df` → **80% train / 20% test** (`randomSplit([0.8, 0.2], seed=42)`).
- **Model: Gaussian Naive Bayes** (`modelType="gaussian"`).
- **Hyperparameter grid:** `smoothing ∈ {0.1, 0.5, 1.0}`.
- **`CrossValidator` 10-fold** (seed 42), metric **accuracy**.
- Ambil `bestModel` dari cross-validation, lalu transform `test_df` → `prediction_test`.

### 5.3 Evaluasi — `evaluate.py`

Hitung terhadap `prediction_test`:

- **Accuracy** (`accuracy`).
- **Precision** (`weightedPrecision`).
- **Recall** (`weightedRecall`).
- **F1-Score** (`f1`).
- **Confusion Matrix** (group by `label`, `prediction`).

Semua hasil dicatat ke log dan dibawa sebagai `evaluation_result` untuk registry.

### 5.4 Model Registry — `registry.py`

- Simpan `bestModel` ke **`models/gaussian_nb`** (`NaiveBayesModel.save`), hapus versi lama dulu.
- Tulis metadata ke **`models/metadata.txt`**: tanggal, algoritma, accuracy, precision, recall, F1.

### 5.5 Prediksi — `predict.py`

- Baca `feature_store.inference_dataset`.
- Rekonstruksi pipeline transformasi fitur (StringIndexer gender + VectorAssembler).
- `NaiveBayesModel.load("models/gaussian_nb")` → `model.transform(feature_df)` → DataFrame prediksi (probabilitas + kelas hasil).

---

## 6. API Backend — `backend/api/*` & `main.py`

FastAPI `main.py` mendaftarkan router:

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/upload/` | Upload Excel → simpan ke `data/` → jalankan seluruh pipeline ETL |
| POST | `/pipeline/run` | Jalankan pipeline untuk file di `data/` (default `req_data_rut.xlsx`); validasi path-traversal & ekstensi Excel |
| POST | `/train/` | Training model (placeholder service) |
| POST | `/predict/` | Prediksi (placeholder service) |
| GET | `/dashboard/` | Health-check dashboard |
| GET | `/` | Root API info |

---

## 7. Integrasi & Dashboard

### 7.1 Trino → Superset

- **Trino** (port 8082) membaca catalog Iceberg (`iceberg`) via Hive Metastore (`thrift://hive-metastore:9083`) dan warehouse MinIO.
- **`superset-init`** menjalankan bootstrap idempotent yang mendaftarkan database **"Academic Trino"** dan dataset otomatis:
  - `iceberg.gold.gold_mahasiswa`
  - `iceberg.gold.gold_program_studi`
  - `iceberg.gold.gold_kurikulum`
- **Superset** (port 8088) → login admin dari env `SUPERSET_ADMIN_*`.

### 7.2 Airflow

- DAG `prediction_pipeline` (jadwal `@daily`):
  `start → run_local_spark_pipeline → publish_serving → end`.
- Task `run_local_spark_pipeline` memanggil `http://host.docker.internal:8000/pipeline/run` (FastAPI di host harus aktif).

### 7.3 Port yang Dipakai

| Service | Port |
|---|---|
| MinIO API / Console | 9000 / 9001 |
| Hive Metastore | 9083 |
| Trino | 8082 |
| Superset | 8088 |
| Airflow webserver | 8085 |
| PostgreSQL serving | 5432 |
| PostgreSQL Hive | 5433 |
| PostgreSQL Airflow | 5434 |
| Spark Master UI (opsional) | 8080 |
| Spark History (opsional) | 18080 |

---

## 8. Struktur Kode

```text
main.py                        # entry FastAPI
backend/
  api/                         # upload, pipeline, train, predict, dashboard
  services/pipeline_service.py # orkestrasi E2E
  bronze/bronze.py             # ingest Excel -> bronze.*
  silver/silver.py             # bersihkan & standardisasi -> silver.*
  gold/                        # gold_mahasiswa, gold_prodi, gold_kurikulum
  feature_store/               # training_dataset, inference_dataset
  ml/                          # data_preparation, train, evaluate, predict, registry
  serving/postgres_sink.py     # publish gold -> PostgreSQL
  spark/session.py             # SparkSession (env-driven, Iceberg catalog)
  config/settings.py           # semua konfigurasi dari .env
  utils/logger.py              # logger
docker/
  minio/ spark/ trino/ hive-metastore/ superset/ airflow/ postgres/
scripts/                       # unit test per modul
docs/                          # dokumentasi & plan
data/req_data_rut.xlsx         # dataset mentah
models/                        # model registry (gaussian_nb + metadata.txt)
```

---

## 9. Alur Kerja Harian (Runbook)

```powershell
# 1. Nyalakan service lakehouse
docker compose up -d --build

# 2. Jalankan FastAPI (host)
uvicorn main:app --reload

# 3. Opsional: trigger pipeline manual
Invoke-RestMethod -Method Post http://localhost:8000/pipeline/run

# 4. (Opsional) Training + evaluasi manual via script test
python -m unittest scripts.test_data_preparation scripts.test_train scripts.test_evaluate scripts.test_registry -v

# 5. Buka dashboard
# Superset  : http://localhost:8088
# Trino UI  : http://localhost:8082
# MinIO     : http://localhost:9001
# Airflow   : http://localhost:8085
```

---

## 10. Validasi & Pengujian

- `docker compose config --quiet` → validasi Compose.
- Unit test: `python -m unittest scripts.test_* -v` (4 test dasar lulus: `test_excel_utils`, `test_file_utils`, `test_logger`, `test_superset_config`).
- `python -m compileall -q backend main.py` → cek sintaks.

---

## 11. Catatan Keputusan Teknis

1. **Linkage antar-sheet dibatalkan** — tidak ada kunci penghubung bersih antara Referensi dan KHS.
2. **Spark lokal sebagai default** — keterbatasan RAM (5,9 GB); cluster Docker via profile `spark-docker` tetap disediakan.
3. **Versi Spark diselaraskan ke 3.5** untuk konsistensi semua library Iceberg/Excel.
4. **PostgreSQL serving dipertahankan** demi kompatibilitas pipeline lama, tetapi **bukan** sumber Superset (Trino/Iceberg adalah source of truth).
5. **Hive Metastore** menggunakan Postgres 16 dengan `POSTGRES_HOST_AUTH_METHOD=trust` + driver JDBC 42.7.4 (driver bawaan image Hive 3.1.3 gagal dengan SCRAM PG16).
6. **Artefak besar dibersihkan** (`_recovery_cleanup/`, `DockerDesktopData/`, `spark-tmp/`, tarball Spark) dan ditambahkan ke `.gitignore`.
