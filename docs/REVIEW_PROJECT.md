# Review Project

**Academic Graduation Prediction System — Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa**

| Item | Keterangan |
|---|---|
| Jenis Dokumen | Review Project (internal) |
| Tujuan | Bahan persiapan sebelum bimbingan dan evaluasi keseluruhan implementasi |
| Bahasa | Bahasa Indonesia (formal) |
| Versi | 1.0 |
| Tanggal | Agustus 2026 |

---

## Daftar Isi

1. [Ringkasan Project](#1-ringkasan-project)
2. [Review Arsitektur](#2-review-arsitektur)
3. [Review Bronze](#3-review-bronze)
4. [Review Silver](#4-review-silver)
5. [Review Gold](#5-review-gold)
6. [Review Feature Store](#6-review-feature-store)
7. [Review Machine Learning](#7-review-machine-learning)
8. [Review Dashboard](#8-review-dashboard)
9. [Review API](#9-review-api)
10. [Review Struktur Folder](#10-review-struktur-folder)
11. [Review Coding Style](#11-review-coding-style)
12. [Review Performance](#12-review-performance)
13. [Review Keamanan](#13-review-keamanan)
14. [Review Penelitian](#14-review-penelitian)
15. [Daftar Temuan](#15-daftar-temuan)
16. [Daftar Peningkatan](#16-daftar-peningkatan)
17. [Kesimpulan](#17-kesimpulan)

---

## 1. Ringkasan Project

### 1.1 Tujuan Project

Project ini membangun **sistem prediksi tingkat kelulusan mahasiswa** berbasis Machine Learning dengan mengintegrasikan *Gold Layer* akademik ke *Feature Store*. Data akademik berupa file Excel diolah melalui arsitektur *data lakehouse* berlapis (Bronze → Silver → Gold), disimpan di **Apache Iceberg**, kemudian diintegrasikan ke **Feature Store** untuk melatih model **Gaussian Naive Bayes** yang memprediksi kelulusan mahasiswa dalam dua kelas: **Tepat Waktu** dan **Terlambat**.

Selain model Machine Learning, project ini dilengkapi **Dashboard Web interaktif** (FastAPI + Jinja2 + Bootstrap 5 + Plotly) serta infrastruktur data lakehouse lengkap (MinIO, Hive Metastore, Trino, Airflow, Apache Superset).

### 1.2 Ruang Lingkup

- **Ingest data akademik** dari file Excel (multi-sheet).
- **ETL berlapis**: Bronze (raw) → Silver (bersih) → Gold (siap analitik).
- **Publish** tabel Gold ke PostgreSQL (*serving layer*) untuk kompatibilitas pipeline lama.
- **Feature Store**: pembuatan *training dataset* dan *inference dataset*.
- **Machine Learning**: training, evaluasi, model registry, dan prediksi (single & batch).
- **Dashboard Web**: monitoring pipeline, data analitik, feature store, training, prediksi, dan riwayat prediksi.
- **Data Lakehouse**: integrasi MinIO, Hive Metastore, Trino, Superset, dan Airflow via Docker Compose.

### 1.3 Teknologi

| Kategori | Teknologi |
|---|---|
| Bahasa | Python 3.11 |
| Web Framework | FastAPI 0.140, Uvicorn, Jinja2, Starlette |
| Big Data | Apache Spark 3.5.3 (PySpark) |
| Table Format | Apache Iceberg 1.5.2 (Spark Runtime) |
| Frontend | HTML, CSS, Bootstrap 5.3, Plotly 2.35, Font Awesome 6.5, JavaScript (fetch/AJAX) |
| Object Storage | MinIO (kompatibel S3) |
| SQL Engine | Trino 462 |
| Orkestrasi | Airflow (LocalExecutor) |
| BI / Visualisasi | Apache Superset (via Trino) |
| Serving Layer | PostgreSQL 16 |
| Metadata | Hive Metastore 3.1.3 |
| Data Science | pandas, numpy, scikit-learn, openpyxl |
| Container | Docker / Docker Compose |

### 1.4 Pipeline Utama

```text
Excel
  │  (upload via FastAPI)
  ▼
Bronze ──► Silver ──► Gold ──► Feature Store ──► Training ──► Evaluation ──► Registry ──► Prediction ──► Dashboard
  │            │          │          │                 (Gaussian NB)              │
  │            │          │          ▼                                            │
  │            │          │     training_dataset                                  │
  │            │          │     inference_dataset                                 ▼
  │            │          ▼                                            single & batch (dashboard)
  │            │    PostgreSQL (serving) + Trino ──► Superset
  ▼
Iceberg (Bronze/Silver/Gold/feature_store namespaces)
```

---

## 2. Review Arsitektur

### 2.1 Alur Implementasi Saat Ini

```text
Excel → Bronze → Silver → Gold → Feature Store → Training → Evaluation → Registry → Prediction → Dashboard
```

### 2.2 Fungsi Setiap Layer

| Layer | File Utama | Fungsi |
|---|---|---|
| **Excel** | `data/*.xlsx` | Sumber data akademik (multi-sheet: Data Referensi Mahasiswa, Data Kurikulum, Data Program Studi, dsb.). Diunggah melalui `POST /upload/*`. |
| **Bronze** | `backend/bronze/bronze.py` | *Raw layer*. Membaca seluruh sheet Excel, menyimpan apa adanya ke tabel Iceberg namespace `bronze` dengan nama tabel diturunkan dari nama sheet. |
| **Silver** | `backend/silver/silver.py` | *Clean layer*. Membersihkan nama kolom, trim spasi, menghapus baris kosong seluruh kolom, dan validasi ringan khusus tabel mahasiswa. |
| **Gold** | `backend/gold/*.py` | *Business layer*. Konversi tipe data, perhitungan *business rule* (estimasi semester, persentase SKS, lama studi, status kelulusan). |
| **Feature Store** | `backend/feature_store/*.py` | Memisahkan data siap model menjadi *training dataset* (mahasiswa lulus) dan *inference dataset* (mahasiswa aktif). |
| **Training** | `backend/ml/train.py` | Melatih Gaussian Naive Bayes dengan Grid Search (smoothing) + Cross Validation. |
| **Evaluation** | `backend/ml/evaluate.py` | Menghitung accuracy, precision, recall, F1, confusion matrix. |
| **Registry** | `backend/ml/registry.py` | Menyimpan model terbaik ke `models/gaussian_nb` beserta metadata. |
| **Prediction** | `backend/ml/predict.py`, `backend/services/prediction_service.py`, `batch_prediction_service.py` | Prediksi single & batch memakai model dari registry, dengan fallback heuristik jika model tidak tersedia. |
| **Dashboard** | `backend/api/pages.py`, `dashboard_data.py`, `frontend/` | Halaman web analitik yang mengonsumsi endpoint JSON `/dashboard-data/*`. |

### 2.3 Kesesuaian Implementasi

Arsitektur berlapis yang diimplementasikan **sesuai dengan alur penelitian** (Gold → Feature Store → ML → Prediksi). Beberapa catatan:

- **Sudah sesuai**: Pemisahan training/inference dataset, business rule di Gold, penyimpanan model ke registry, dan dashboard sebagai konsumen akhir.
- **Perlu diperhatikan**: Alur *Serving* tambahan (Gold → PostgreSQL → Superset) merupakan pelengkap dari luar scope utama ML, namun tetap selaras dengan visi *data lakehouse* dan kompatibilitas pipeline lama.
- **Alur async**: Pipeline dapat dijalankan synchronous (`/pipeline/run`) maupun asynchronous dengan monitoring per tahap (`/pipeline/start` + `/pipeline/state`).

---

## 3. Review Bronze

### 3.1 Input

- File Excel (`.xlsx`/`.xls`) yang diunggah ke folder `data/`.
- Seluruh *sheet* pada file Excel dibaca otomatis.

### 3.2 Output

- Satu tabel Iceberg per *sheet* di namespace `iceberg.bronze.<table_name>`.
- Nama tabel diturunkan dari nama sheet (`excel_sheet_to_table`) — huruf kecil, spasi/simbol diganti `_`.

### 3.3 Transformasi

- Nama sheet → nama tabel Iceberg.
- Pembacaan data via pandas (preview/validasi awal) dan Spark (`spark-excel` dengan `inferSchema=true`).
- Ditulis ulang dengan `createOrReplace()` (overwrite penuh).

### 3.4 Validasi

- Sheet yang gagal dibaca → dilewati (skipped) dengan log warning.
- Sheet kosong → dilewati.
- Sheet tanpa kolom → dilewati.
- Tidak ada validasi tipe data, *deduplication*, atau *schema enforcement* di layer ini (sesuai konsep raw layer).

### 3.5 Kelebihan

- Generik: semua sheet ter-*ingest* otomatis tanpa hardcode.
- Logging ringkasan (total berhasil / skip) memudahkan debugging.
- Membaca ulang dengan Spark memastikan data ter-distribusi untuk proses selanjutnya.

### 3.6 Kekurangan

- `inferSchema=true` dapat menghasilkan tipe yang tidak konsisten antarsheet/data.
- `createOrReplace()` menghapus data lama; tidak ada *versioning* eksplisit di sisi aplikasi (Iceberg menyimpan snapshot, tetapi ditimpa).
- Tidak ada validasi *required columns*; sheet dengan struktur salah baru terdeteksi di layer Gold/Feature Store.
- Nama file tidak dipakai; hanya nama sheet yang menjadi identitas tabel → dua file berbeda dengan nama sheet sama akan bertabrakan.

### 3.7 Rekomendasi

- Tambahkan *schema validation* ringan (minimal daftar kolom penting per sheet).
- Pertimbangkan strategi *incremental append* atau *partitioning* sesuai kebutuhan penelitian.
- Dokumentasikan daftar sheet yang diharapkan dari file Excel template.

---

## 4. Review Silver

### 4.1 Proses Cleaning

- **Rename kolom**: seluruh kolom dibersihkan (`clean_column_name`) menjadi `snake_case` ASCII.
- **Trim**: seluruh kolom bertipe string di-`trim()` untuk menghapus spasi tepi.
- **Baris kosong**: baris yang seluruh kolomnya `null` dihapus (`df.na.drop(how="all")`).

### 4.2 Standardisasi

- Nama kolom distandarkan menjadi format konsisten (`lowercase`, `_`, tanpa karakter khusus).
- Proses berlaku seragam untuk semua tabel Bronze.

### 4.3 Validasi Data

- Khusus tabel `data_referensi_mahasiswa`: baris tanpa `tanggal_masuk` dihapus.
- Tidak ada validasi *constraint* bisnis lain di layer ini.

### 4.4 Transformasi

- Perubahan tipe data **tidak** dilakukan di Silver (dilakukan di Gold).
- Hasil ditulis ke namespace `silver` dengan `createOrReplace()`.

### 4.5 Kelebihan

- Pembersihan nama kolom konsisten → mempermudah layer berikutnya.
- Kode sederhana, mudah dibaca, dan generik untuk semua tabel.

### 4.6 Kekurangan

- Validasi masih sangat tipis; data dengan format salah (mis. IPK non-numerik) lolos hingga Gold.
- Tidak ada *data quality* report (jumlah baris dibuang, persentase missing per kolom).
- `createOrReplace()` membuat layer Silver tidak memiliki riwayat.

### 4.7 Rekomendasi

- Tambahkan *data quality metrics* pada log (missing %, rows dropped).
- Pindahkan validasi nilai (rentang IPK 0–4, SKS > 0) ke Silver agar Gold lebih bersih.
- Pertimbangkan penyimpanan statistik kualitas data per eksekusi untuk bahan laporan penelitian.

---

## 5. Review Gold

### 5.1 Business Rule

- **Lama studi (bulan)**: `ceil(months_between(tanggal_keluar|hari_ini, tanggal_masuk))` — menggunakan tanggal keluar jika sudah lulus, atau hari ini jika masih aktif.
- **Estimasi semester**: `ceil(lama_studi_bulan / 6)`.
- **Persentase SKS**: `(total_sks / jumlah_sks_kurikulum) * 100`, dengan `jumlah_sks_kurikulum` diambil dari tabel kurikulum.
- **Status kelulusan** (label):
  - Mahasiswa dengan status `LULUS` dan `estimasi_semester <= 8` → **Tepat Waktu**.
  - Mahasiswa dengan status `LULUS` dan `estimasi_semester > 8` → **Terlambat**.
  - Selain itu → `null`.

### 5.2 Feature Engineering

- Konversi tipe data (IPK → double, SKS/jumlah MK → int, tanggal → date).
- Normalisasi `status_mahasiswa` (trim + uppercase saat penentuan label).
- Perhitungan feature turunan: `lama_studi_bulan`, `estimasi_semester`, `persentase_sks`, `status_kelulusan`.

### 5.3 Feature yang Dibuat

| Feature | Sumber | Tipe | Deskripsi |
|---|---|---|---|
| `jenis_kelamin` | Silver | string | Jenis kelamin mahasiswa (L/P). |
| `ipk` | Silver | double | Indeks Prestasi Kumulatif. |
| `total_sks` | Silver | int | Total SKS yang ditempuh. |
| `jumlah_mk` | Silver | int | Jumlah mata kuliah yang diambil. |
| `lama_studi_bulan` | turunan | int | Lama studi dalam bulan (bulat ke atas). |
| `estimasi_semester` | turunan | int | Estimasi semester (bulan/6, dibulatkan ke atas). |
| `persentase_sks` | turunan | double | `total_sks / sks_kurikulum * 100`. |
| `status_kelulusan` | turunan | string | Label: `Tepat Waktu` / `Terlambat`. |

### 5.4 Alasan Feature Dibuat

- `estimasi_semester` dan `persentase_sks` merepresentasikan progres studi secara kuantitatif.
- `ipk`, `total_sks`, `jumlah_mk`, `jenis_kelamin` merupakan atribut akademik standar yang umum digunakan pada penelitian prediksi kelulusan.
- Label `status_kelulusan` dibangun dari *business rule* ketepatan waktu (≤ 8 semester).

### 5.5 Kelebihan

- Business rule terdokumentasi jelas dan terpusat di satu modul.
- Label & feature utama selaras dengan tujuan penelitian (ketepatan waktu kelulusan).
- `gold_mahasiswa` menyimpan statistik distribusi (lulus/aktif/null semester) untuk verifikasi.

### 5.6 Kekurangan

- `gold_program_studi` dan `gold_kurikulum` hanya *passthrough* dari Silver (belum ada agregasi/transformasi bisnis yang bermakna).
- `jumlah_sks_kurikulum` diambil dari baris pertama tabel kurikulum (`first()[0]`) — akan error bila tabel kosong atau lebih dari satu kurikulum.
- Rule `estimasi_semester <= 8` bersifat hardcoded dan hanya asumsi; perlu dibuktikan dari data/kebijakan akademik.
- Label biner (Tepat/Terlambat) mengabaikan kelas lain (mis. status non-lulus) — disengaja untuk binary classification, namun perlu dijelaskan di penelitian.

### 5.7 Rekomendasi

- Definisikan `jumlah_sks_kurikulum` secara eksplisit (mis. per program studi) bila dataset memiliki lebih dari satu kurikulum.
- Simulasikan sensitivitas ambang 8 semester dan laporkan alasannya.
- Tambahkan agregasi bisnis pada gold program studi (mis. jumlah mahasiswa per prodi per tahun) bila diperlukan analitik.

---

## 6. Review Feature Store

### 6.1 Training Dataset

- Sumber: `gold.gold_mahasiswa`.
- Filter: `status_mahasiswa == "LULUS"`.
- Menghapus baris dengan *feature/label null* (6 feature + label).
- Kolom: `jenis_kelamin, estimasi_semester, ipk, total_sks, jumlah_mk, persentase_sks, status_kelulusan` (6 feature + 1 label).

### 6.2 Inference Dataset

- Sumber: `gold.gold_mahasiswa`.
- Filter: `status_mahasiswa == "AKTIF"`.
- Menghapus baris dengan *feature null*.
- Kolom: 6 feature (tanpa label).

### 6.3 Alasan Dipisah

- **Training dataset** membutuhkan label (`status_kelulusan`) yang hanya dimiliki mahasiswa lulus → dipakai untuk melatih dan mengevaluasi model.
- **Inference dataset** adalah mahasiswa aktif yang belum memiliki label → target prediksi di masa mendatang (objek prediksi).
- Pemisahan menjaga *data leakage* (label dari masa depan tidak bocor ke objek prediksi) dan menyelaraskan domain training vs. produksi.

### 6.4 Feature yang Digunakan

| Feature | Tipe | Dipakai Training | Dipakai Inference |
|---|---|---|---|
| `jenis_kelamin` | string | Ya | Ya |
| `estimasi_semester` | int | Ya | Ya |
| `ipk` | double | Ya | Ya |
| `total_sks` | int | Ya | Ya |
| `jumlah_mk` | int | Ya | Ya |
| `persentase_sks` | double | Ya | Ya |
| `status_kelulusan` (label) | string | Ya | Tidak |

### 6.5 Apakah Sudah Sesuai

**Sudah sesuai** dengan prinsip feature store: konsistensi feature antara training dan inference (kolom identik), sumber data tunggal (Gold), dan pemisahan label. Catatan:

- Belum ada *feature versioning* / metadata feature (mis. skema, definisi, pemilik) seperti feature store industri (Feast, Tecton). Untuk skala penelitian hal ini wajar.
- Penyimpanan masih berupa tabel Iceberg biasa, bukan *feature repository* khusus.

---

## 7. Review Machine Learning

### 7.1 Preprocessing

File: `backend/ml/data_preparation.py`

- Membaca `feature_store.training_dataset`.
- Menampilkan distribusi label untuk pengecekan.
- Membangun **Pipeline** Spark ML: `StringIndexer` (jenis_kelamin, label) → `VectorAssembler`.

### 7.2 StringIndexer

- `jenis_kelamin` → `jenis_kelamin_index`.
- `status_kelulusan` → `label`.
- Menggunakan `handleInvalid="keep"` sehingga nilai tak dikenal dipetakan ke indeks khusus (tidak crash).
- **Catatan**: urutan label mengikuti frekuensi menurun (default `frequencyDesc`), sehingga pemetaan indeks ↔ label di sisi prediksi harus di-resolve ulang (`prediction_service._resolve_label_order`). Ini adalah titik rapuh yang bergantung pada distribusi data.

### 7.3 VectorAssembler

- Menggabungkan: `jenis_kelamin_index, estimasi_semester, ipk, total_sks, jumlah_mk, persentase_sks` → kolom `features`.

### 7.4 Train Test Split

- `randomSplit([0.8, 0.2], seed=42)`.
- **Catatan**: tanpa stratifikasi dan tanpa *class balance*; untuk dataset dengan kelas tidak seimbang dapat memengaruhi evaluasi.

### 7.5 Cross Validation

- `CrossValidator` dengan **10 folds**, `seed=42`, metrik `accuracy`.
- Grid Search: `smoothing` ∈ {0.1, 0.5, 1.0} (3 kombinasi).

### 7.6 Gaussian Naive Bayes

- `NaiveBayes(modelType="gaussian")`.
- Menghasilkan `prediction`, `probability`, `rawPrediction`.
- Model terbaik dipilih dari hasil cross validation.

### 7.7 Evaluation

File: `backend/ml/evaluate.py`

- Metrik: **Accuracy, Precision (weighted), Recall (weighted), F1**.
- Confusion matrix (groupBy label/prediction).
- ROC curve & AUC dihitung di `backend/services/training_metrics.py` (Python murni, tanpa sklearn) dan ditampilkan pada halaman Training.

### 7.8 Registry

File: `backend/ml/registry.py`

- Menghapus model lama, menyimpan model terbaik ke `models/gaussian_nb`.
- Menyimpan `models/metadata.txt` (tanggal, algoritma, accuracy, precision, recall, F1).
- **Catatan**: registry bersifat *local filesystem*, belum ada model serving API terpisah (inference langsung memuat file).

### 7.9 Prediction

File: `backend/ml/predict.py`, `backend/services/prediction_service.py`, `batch_prediction_service.py`

- `predict.py`: membaca `inference_dataset` dari Iceberg, membangun ulang pipeline feature, memuat model, transform.
- `prediction_service.predict_single`: prediksi satu mahasiswa (dari form), dengan fallback heuristik (`estimasi_semester <= 8`) jika model belum tersedia.
- `batch_prediction_service.predict_dataset`: prediksi batch dari file Excel yang diunggah (menghitung fitur dengan logika yang sama dengan Gold).
- Urutan label di-resolve dari distribusi training dataset (cache 5 menit).

### 7.10 Analisis Apakah Pipeline ML Sudah Baik

**Sudah baik secara struktur** (preprocessing → split → CV → evaluasi → registry → prediksi) dan sesuai praktik standar. Namun terdapat beberapa catatan penting:

| Aspek | Status | Catatan |
|---|---|---|
| Struktur pipeline | Baik | Urutan baku dan modular. |
| Cross validation | Baik | 10-fold + grid smoothing. |
| Evaluasi | Cukup | Hanya accuracy sebagai *tuning metric*; disarankan tambah F1/ROC-AUC (imbalance). |
| Class imbalance | Perlu perhatian | Tidak ada *classWeight* / resampling; untuk label biner yang tidak seimbang, accuracy bisa menyesatkan. |
| Pemetaan label | Rapuh | Bergantung pada `frequencyDesc`; perlu disimpan eksplisit (mis. di metadata registry). |
| Generalisasi | Belum dibuktikan | Belum ada evaluasi pada dataset luar / data waktu berikutnya. |
| Reproducibility | Baik | Seed tetap (42), grid terdokumentasi. |

---

## 8. Review Dashboard

### 8.1 Struktur Frontend

- **Template engine**: Jinja2 (FastAPI `Jinja2Templates`).
- **Layout**: `base.html` → `partials/sidebar.html`, `partials/topbar.html`, `partials/footer.html`.
- **Halaman** (`frontend/templates/pages/`): `dashboard`, `upload`, `pipeline`, `feature_store`, `training`, `prediction`, `history`, `about`.
- **Asset statis**: `frontend/static/css/app.css` (design system indigo `#6366f1`), `frontend/static/js/app.js` (helpers `formatNumber`, `formatBytes`, `formatDateTime`, `renderPlot`).
- **Library eksternal**: Bootstrap 5.3, Plotly 2.35, Font Awesome 6.5, Google Fonts (Inter).

### 8.2 Navigasi

- Sidebar dikelompokkan menjadi 3 seksi:
  - **Menu Utama**: Dashboard, Upload Dataset, Pipeline Monitoring.
  - **Data & Model**: Feature Store, Training Model, Prediction.
  - **Lainnya**: History Prediction, Tentang Penelitian.
- Sidebar responsif (collapsible di desktop, drawer + backdrop di mobile).

### 8.3 UX

- Dashboard menggunakan **AJAX/fetch tanpa reload** (`/dashboard-data/summary`), dengan polling 60 detik dan tombol "Muat Ulang".
- State loading (`spinner`), state kosong ("Data belum tersedia…"), dan state error ditangani di sisi JS.
- Halaman Upload: daftar file + tombol "Jalankan Pipeline".
- Halaman Pipeline: monitoring per tahap (Waiting/Running/Success/Failed) via `GET /pipeline/state`.
- Halaman Prediction: drag-drop upload + XHR progress, form prediksi satu mahasiswa, dan hasil batch per-mahasiswa.
- Indikator mode Spark ditampilkan pada sidebar footer ("Spark local"/"Spark cluster").

### 8.4 UI

- Design system konsisten: kartu (`.card`), KPI (`.kpi-card`, `.kpi-value`), chip status, badge, palet warna `#6366f1` (indigo) sebagai warna primer.
- Warna semantik untuk prediksi: hijau `#10b981` (Tepat Waktu), merah `#ef4444` (Terlambat), dengan class pendukung (`.text-success-c`, `.badge-soft-success`, dst.).
- Responsif (breakpoints 1199.98 / 991.98 / 575.98 px) dengan override di `app.css`.

### 8.5 Visualisasi (Plotly)

| Halaman | Grafik |
|---|---|
| Dashboard | Pie status mahasiswa, Bar jenis kelamin, Bar semester, Line tren masuk, Histogram IPK, Histogram SKS, Distribusi kelulusan, Gauge % tepat waktu. |
| Feature Store | Statistik kolom numerik (mean/std/min/max), preview data. |
| Training | KPI (accuracy, precision, recall, F1, AUC), confusion matrix, ROC curve + AUC badge. |
| Prediction | Bar distribusi hasil, KPI total/tepat/terlambat, tabel per-mahasiswa dengan badge + probabilitas. |

### 8.6 Endpoint yang Dipakai Halaman

| Halaman | Endpoint |
|---|---|
| Dashboard | `GET /dashboard-data/summary` |
| Feature Store | `GET /dashboard-data/feature-store` |
| Upload | `POST /upload/file`, `POST /pipeline/start` |
| Pipeline | `POST /pipeline/start`, `GET /pipeline/state` |
| Training | `POST /train/run` |
| Prediction | `POST /predict/submit`, `POST /predict/dataset` |
| History | halaman server-side (Jinja2) — `GET /history` |

---

## 9. Review API

Semua endpoint terdaftar pada aplikasi FastAPI (`main.py`). Halaman web (Jinja2) tidak muncul di OpenAPI karena `include_in_schema=False`.

### 9.1 Endpoint API (JSON)

| No | Endpoint | Method | Fungsi | Status |
|---|---|---|---|---|
| 1 | `/` | GET | Status API root. | ✅ Aktif |
| 2 | `/upload/` | POST | Upload Excel + langsung menjalankan pipeline penuh. | ✅ Aktif |
| 3 | `/upload/file` | POST | Upload Excel hanya menyimpan file (tanpa pipeline). | ✅ Aktif |
| 4 | `/train/` | POST | Health check Training API. | ✅ Aktif |
| 5 | `/train/run` | POST | Menjalankan training penuh (prep → train → evaluate → registry) + ROC. | ✅ Aktif* |
| 6 | `/predict/` | POST | Health check Prediction API. | ✅ Aktif |
| 7 | `/predict/submit` | POST | Prediksi satu mahasiswa + simpan riwayat. | ✅ Aktif |
| 8 | `/predict/dataset` | POST | Prediksi batch dari file Excel di `data/`. | ✅ Aktif |
| 9 | `/dashboard/` | GET | Health check Dashboard API. | ✅ Aktif |
| 10 | `/dashboard-data/summary` | GET | Ringkasan KPI & data chart dari Gold (cache 60 dtk). | ✅ Aktif* |
| 11 | `/dashboard-data/feature-store` | GET | Ringkasan training/inference dataset (cache 60 dtk). | ✅ Aktif* |
| 12 | `/pipeline/run` | POST | Menjalankan pipeline synchronous. | ✅ Aktif |
| 13 | `/pipeline/start` | POST | Menjalankan pipeline asynchronous (background thread). | ✅ Aktif |
| 14 | `/pipeline/state` | GET | Status setiap tahap pipeline. | ✅ Aktif |

*\*) Bergantung pada Spark/Iceberg aktif. Di mesin lokal Windows (tanpa Hive Metastore/MinIO), endpoint berisi inisialisasi Spark dapat hang atau gagal memuat model — keterbatasan lingkungan, bukan kesalahan kode.*

### 9.2 Endpoint Halaman (Jinja2)

| No | Route | Method | Fungsi |
|---|---|---|---|
| 15 | `/` | GET | Redirect ke `/dashboard`. |
| 16 | `/dashboard` | GET | Halaman dashboard. |
| 17 | `/upload` | GET | Halaman upload dataset. |
| 18 | `/pipeline` | GET | Halaman monitoring pipeline. |
| 19 | `/feature_store` | GET | Halaman feature store. |
| 20 | `/training` | GET | Halaman training model. |
| 21 | `/prediction` | GET | Halaman prediksi. |
| 22 | `/history` | GET | Halaman riwayat prediksi (query `q`, `status`). |
| 23 | `/about` | GET | Halaman tentang penelitian. |
| 24 | `/static/*` | GET | Asset statis (CSS, JS) via `StaticFiles`. |

---

## 10. Review Struktur Folder

| Folder / File | Fungsi |
|---|---|
| `main.py` | Entry point FastAPI; membuat aplikasi, mount static, mendaftarkan seluruh router. |
| `backend/` | Inti aplikasi backend. |
| `backend/api/` | Router FastAPI (upload, train, predict, dashboard, dashboard_data, pipeline, pages). |
| `backend/bronze/` | Modul layer Bronze (ingest Excel → Iceberg). |
| `backend/silver/` | Modul layer Silver (cleaning & standardisasi). |
| `backend/gold/` | Modul layer Gold (business rule, feature engineering). |
| `backend/feature_store/` | Modul pembuatan training & inference dataset. |
| `backend/ml/` | Modul machine learning (data_preparation, train, evaluate, registry, predict). |
| `backend/services/` | Layanan tingkat aplikasi (pipeline_service, pipeline_runner, pipeline_state, dashboard_service, prediction_service, batch_prediction_service, history_service, training_metrics). |
| `backend/serving/` | *Serving layer*: publish tabel Gold ke PostgreSQL (kompatibilitas Superset). |
| `backend/spark/` | Konfigurasi & pembuatan SparkSession (local/cluster, Iceberg catalog). |
| `backend/config/` | Konfigurasi project & environment (`.env` loader, settings). |
| `backend/utils/` | Utilitas (logger, excel_utils, file_utils). |
| `frontend/` | Aplikasi web: `templates/` (Jinja2) + `static/` (CSS/JS). |
| `frontend/templates/pages/` | Halaman-halaman dashboard. |
| `frontend/templates/partials/` | Komponen bersama (sidebar, topbar, footer). |
| `scripts/` | Unit test (`test_*.py`) dan script debug manual (`cek_*.py`, `check_*.py`). |
| `models/` | Model registry (`gaussian_nb/`) + metadata. |
| `data/` | File Excel input + riwayat prediksi (`data/history/predictions.json`). |
| `docker/` | Konfigurasi Docker untuk seluruh service data lakehouse (airflow, hive-metastore, minio, postgres, spark, superset, trino). |
| `docker-compose.yml` | Orkestrasi seluruh service (Postgres, Redis, MinIO, HMS, Trino, Airflow, Superset). |
| `docs/` | Dokumentasi project (ALUR_PENGERJAAN, REVIEW_PROJECT). |
| `iceberg/` | Warehouse Iceberg mode `local` (filesystem). |
| `logs/` | Log aplikasi. |
| `spark-events/` | Event log Spark (untuk History Server). |
| `spark-tmp/` | Direktori kerja sementara Spark (local dirs). |
| `requirements.txt` | Dependency Python. |
| `.env` / `.env.example` | Konfigurasi environment (credential lokal; template publik). |
| `README.md` | Dokumentasi penggunaan & arsitektur. |

---

## 11. Review Coding Style

### 11.1 Duplicate Code

- `backend/feature_store/inference_dataset.py` dan `backend/feature_store/training_dataset.py` memiliki blok pembacaan Gold + distribusi yang identik (±21 baris). **Sengaja dipertahankan** untuk menghindari perubahan logika pipeline; dapat di-refactor ke helper bersama.
- `backend/ml/data_preparation.py` dan `backend/ml/predict.py` memiliki pola *assembler/string indexer* yang serupa (±19 baris). Keduanya membangun ulang pipeline feature — duplikasi ini perlu disinkronkan secara hati-hati agar tetap konsisten.
- `prediction_service.py` dan `batch_prediction_service.py` memiliki pola `_model_exists`, `_build_input_frame`, resolusi label yang hampir identik.

### 11.2 Unused Import

- Audit `pyflakes` menemukan **1 isu nyata** pada `backend/services/pipeline_runner.py` (variabel `exc` ter-assign tapi tidak dipakai) — **sudah diperbaiki**.
- Tidak ditemukan unused import bermakna lainnya pada modul inti.

### 11.3 File Terlalu Panjang

- Tidak ada file Python yang sangat panjang (terbesar `dashboard_service.py` 249 baris, `batch_prediction_service.py` 318 baris) — masih dalam batas wajar.

### 11.4 Fungsi Terlalu Panjang

- `compute_features` (batch_prediction_service, ±60 baris) dan `compute_dashboard_payload` dapat dipecah, namun masih mudah dibaca.
- `bronze.load_all_sheets_to_bronze` cukup panjang tetapi linear dan jelas.

### 11.5 Naming

- **Baik**: nama modul/fungsi deskriptif (`load_all_sheets_to_bronze`, `process_gold_mahasiswa`, `predict_single`).
- **Beragam gaya**: beberapa fungsi memakai `snake_case` konsisten; sejumlah blok log komentar `# ====` menambah keterbacaan.
- **Catatan**: terdapat komentar separasi `# ====` yang berlebihan di banyak file; konsisten tapi bisa disederhanakan.

### 11.6 Struktur Project

- **Baik**: pemisahan tegas antara `api` (HTTP), `services` (logika aplikasi), `ml` (ML), dan layer ETL (`bronze/silver/gold/feature_store`).
- **Catatan**: `backend/services/pipeline_service.py` dan `backend/services/pipeline_runner.py` mengeksekusi urutan modul yang sama (duplikasi urutan pipeline); disarankan satu *orchestrator* bersama agar tidak drif.

### 11.7 Kesimpulan Coding Style

Secara umum **rapi, modular, dan mudah dipahami**. Prioritas perbaikan: mengurangi duplikasi logika feature/preprocessing agar training dan inference tidak menyimpang, serta memusatkan urutan pipeline.

---

## 12. Review Performance

### 12.1 Spark

- SparkSession dikonfigurasi driver/executor memory 4g, `spark.sql.shuffle.partitions=8`.
- **Catatan**: `get_spark()` menghentikan session aktif dan membuat ulang di hampir setiap pemanggilan (dashboard, prediction, pipeline). Membuat ulang SparkSession berulang kali berbiaya besar.
- Batch prediction memakai `pandas.iterrows()` pada file besar (data mahasiswa puluhan ribu baris) — lambat dibandingkan operasi vektorisasi.

### 12.2 Iceberg

- Semua layer ditulis sebagai tabel Iceberg dengan `createOrReplace()` (overwrite).
- `cache-enabled=false` untuk catalog Hive — query berulang melakukan koneksi ke HMS.

### 12.3 Docker

- Stack lengkap (MinIO, HMS, Trino, Airflow, Superset, Postgres, Redis) dengan profile `spark-docker` untuk Spark master/worker/history (opsional).
- Memori dibatasi per service (`mem_limit`).

### 12.4 FastAPI

- Endpoint pipeline synchronous (`/pipeline/run`) memblokir hingga pipeline selesai (lama). Versi async (`/pipeline/start`) sudah tersedia dan lebih tepat untuk UI.
- Dashboard menggunakan cache 60 detik (in-memory, dengan lock) — mencegah hammering Spark.

### 12.5 Memory

- Prediksi single membangun DataFrame + fit StringIndexer/VectorAssembler per request — overhead kecil namun tidak efisien jika dipanggil masif.
- Riwayat prediksi disimpan sebagai satu file JSON (`data/history/predictions.json`) yang terus bertambah; dibaca seluruhnya setiap request History.

### 12.6 Bottleneck

1. **Inisialisasi Spark** di setiap request (dashboard, prediction) — bottleneck utama pada lingkungan tanpa Spark yang selalu hidup.
2. **`pandas.iterrows()`** pada batch prediction untuk dataset besar.
3. **Full `collect()`** di dashboard_service (groupBy + collect untuk tiap grafik) — tidak skalabel untuk data sangat besar.
4. **`createOrReplace()`** — tidak ada incremental processing; seluruh layer ditulis ulang tiap eksekusi.
5. **Memuat model dari disk** setiap prediksi (`NaiveBayesModel.load`) tanpa cache di memori.

---

## 13. Review Keamanan

### 13.1 Upload File

- Ekstensi divalidasi (`.xlsx`/`.xls`) pada `upload.py`.
- **Risiko**: nama file dari user dipakai langsung sebagai path (`UPLOAD_DIR / file.filename`) tanpa sanitasi — berpotensi *path traversal* bila filename berisi `..\` atau path absolut. Endpoint `/pipeline/*` sudah memvalidasi (`candidate.name == filename`), tetapi `/upload/*` belum.
- Tidak ada batas ukuran file.
- Tidak ada autentikasi/otorisasi pada seluruh endpoint.

### 13.2 Validasi Input

- `predict.py` menggunakan Pydantic model dengan tipe, namun **tanpa batasan rentang** (IPK bisa > 4, SKS bisa negatif, estimasi_semester tidak dibatasi).
- Batch prediction melewati baris dengan nilai tidak valid, tetapi tidak melaporkan jumlah yang dilewati.

### 13.3 Logging

- Logger console sederhana (`backend/utils/logger.py`) — informasi cukup, tidak memuat data sensitif.
- Tidak ada rotasi log atau penyimpanan log ke file secara otomatis.

### 13.4 Error Handling

- Endpoint membungkus error menjadi `HTTPException` dengan `detail=str(e)` — pada beberapa endpoint detail exception internal **bocor ke client** (informasi internal).
- Pipeline async menangkap error dan menandai tahap gagal pada `/pipeline/state` (baik).

### 13.5 Catatan Kredensial

- `.env` tidak di-commit (sesuai README); `.env.example` hanya berisi nilai default dev.
- Credential MinIO/Postgres/Superset menggunakan nilai default (`change-me`, `minioadmin`) — hanya untuk development, wajib diganti di produksi.

---

## 14. Review Penelitian

### Judul Penelitian

> **"Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa Berbasis Machine Learning"**

### 14.1 Apakah Sudah Sesuai

| Komponen Judul | Implementasi | Kesesuaian |
|---|---|---|
| Gold Layer Akademik | `backend/gold/*` membangun tabel gold (mahasiswa, prodi, kurikulum) dengan business rule | ✅ Sesuai |
| Integrasi ke Feature Store | `backend/feature_store/*` membaca Gold → training & inference dataset | ✅ Sesuai |
| Model Prediksi Tingkat Kelulusan | Gaussian Naive Bayes biner (Tepat Waktu / Terlambat) | ✅ Sesuai |
| Machine Learning | Pipeline training → evaluasi → registry → prediksi | ✅ Sesuai |
| Konteks (akademik) | Dataset mahasiswa ITERA (IPK, SKS, semester, jenis kelamin) | ✅ Sesuai |

### 14.2 Apakah Ada yang Keluar dari Scope

- **Dashboard Web, Superset, Airflow, Trino, serving ke PostgreSQL** merupakan fitur tambahan di luar inti "Gold → Feature Store → ML". Ini **tidak menyimpang** melainkan memperluas nilai implementasi (visualisasi hasil, orkestrasi, data lakehouse) dan umumnya dianggap nilai tambah untuk penelitian tugas akhir. Namun perlu dijelaskan di laporan sebagai *value-added*, bukan bagian dari kontribusi inti.
- Penggunaan **Apache Iceberg + MinIO + Hive Metastore** memperkuat konteks *data lakehouse*, relevan dengan pendekatan modern.

### 14.3 Apakah Ada yang Kurang

| Aspek | Kondisi | Kebutuhan |
|---|---|---|
| Pembuktian performa model | Metrik internal ada (acc/precision/recall/F1/AUC), namun belum ada *benchmark* vs model pembanding (mis. Logistic Regression, Decision Tree) | Menambahkan perbandingan model memperkuat klaim penelitian. |
| Dataset aktual vs contoh | Dataset saat ini `req_data_rut.xlsx` (file template) | Pastikan dataset akhir penelitian ter-*ingest* dan hasilnya terdokumentasi. |
| Interpretasi hasil | Belum ada pembahasan tentang feature yang paling berpengaruh | Analisis korelasi/feature importance mendukung bab pembahasan. |
| Reproducibility eksperimen | Seed & grid tercatat, tetapi belum ada *experiment log* terpusat | Simpan snapshot konfigurasi + metrik tiap percobaan. |
| Pembahasan imbalanced data | Tidak diatasi | Perlu diskusi di laporan (kelas Tepat/Terlambat). |

### 14.4 Kesimpulan Penelitian

Implementasi **sudah sesuai** dengan judul dan alur penelitian. Fitur tambahan (dashboard, lakehouse, Superset) berada di luar scope inti namun meningkatkan kualitas sistem. Hal yang **kurang** terutama pada aspek *eksperimen* (perbandingan model, feature analysis, dokumentasi hasil pada dataset final) — penting untuk melengkapi laporan tugas akhir.

---

## 15. Daftar Temuan

| No | Temuan | Dampak | Prioritas | Solusi |
|---|---|---|---|---|
| 1 | Filename upload tanpa sanitasi path (`upload.py`) | Risiko path traversal / menimpa file | **Tinggi** | Sanitasi filename (reuse pola `resolve_pipeline_file`), batasi ukuran file. |
| 2 | Detail exception `str(e)` bocor ke client pada beberapa endpoint | Informasi internal terekspos | **Tinggi** | Kembalikan pesan generik + log detail di server. |
| 3 | Tanpa autentikasi/otorisasi pada seluruh endpoint | Akses penuh oleh siapa pun | **Tinggi** | Tambahkan mekanisme auth (minimal untuk env produksi). |
| 4 | `get_spark()` membuat ulang SparkSession tiap request | Overhead besar; penyebab hang endpoint dashboard/prediksi di lokal | **Tinggi** | SparkSession singleton/reuse; pisahkan inisialisasi dari request handler. |
| 5 | Inisialisasi model dibaca dari disk setiap prediksi | Latensi prediksi tinggi | **Sedang** | Cache model di memori (lazy singleton). |
| 6 | Duplikasi pipeline feature antara training & inference (data_preparation vs predict) | Risiko drift feature | **Sedang** | Refactor satu *feature pipeline* bersama. |
| 7 | Duplikasi urutan pipeline (pipeline_service vs pipeline_runner) | Drift urutan antar mode | **Sedang** | Satu orchestrator + daftar tahap. |
| 8 | `pandas.iterrows()` pada batch prediction untuk data besar | Lambat untuk puluhan ribu baris | **Sedang** | Vektorisasi pandas / operasi Spark. |
| 9 | `jumlah_sks_kurikulum` diambil `.first()[0]` tanpa guard | Error bila kurikulum kosong / multi | **Sedang** | Validasi + mekanisme lookup yang jelas. |
| 10 | Riwayat prediksi satu file JSON yang tumbuh tanpa batas | Degradasi performa history | **Sedang** | Gunakan DB (SQLite/Postgres) atau rotasi file. |
| 11 | Tidak ada stratifikasi / penanganan imbalance di train-test | Evaluasi bisa menyesatkan | **Sedang** | Stratify split, tambah metrik F1/ROC-AUC, kelas imbang. |
| 12 | Pemetaan label StringIndexer bergantung `frequencyDesc` | Rapuh bila distribusi berubah | **Sedang** | Simpan mapping label di metadata registry. |
| 13 | `createOrReplace()` di seluruh layer tanpa incremental | Redundan; history hilang | **Rendah** | Pertimbangkan append/partition bila diperlukan. |
| 14 | Duplikasi selector CSS terdeteksi (semua di media query) | Bukan bug; hanya catatan | **Rendah** | Tidak perlu perubahan. |
| 15 | File yatim `scripts/cek_*.py`, `check_*.py` tidak dirujuk dokumentasi | Kebingungan fungsi | **Rendah** | Pindahkan ke `scripts/dev/` atau dokumentasikan. |
| 16 | 2 unit test `test_spark_session` gagal di lokal (konfigurasi Iceberg/Spark) | Tidak terkait kode aplikasi | **Rendah** | Kondisikan test pada env cluster; dokumentasikan. |

---

## 16. Daftar Peningkatan

### High Priority

1. **Sanitasi nama file upload** dan batas ukuran file (endpoint `/upload/*`).
2. **Jangan bocorkan detail exception** ke response client; gunakan pesan generik + log.
3. **Reuse SparkSession** (singleton) dan hindari inisialisasi Spark di dalam setiap request; pertimbangkan pemicu manual / worker terpisah untuk pipeline berat.
4. **Tambahkan autentikasi/otorisasi** minimal sebelum deployment publik.

### Medium Priority

5. **Cache model** di memori (lazy singleton) agar prediksi tidak membaca disk setiap kali.
6. **Satukan feature pipeline** training & inference dalam satu modul (hindari drift).
7. **Pusatkan urutan pipeline** (satu orchestrator; pipeline_service & pipeline_runner memakainya).
8. **Optimalkan batch prediction** (vektorisasi pandas / Spark, bukan `iterrows`).
9. **Tangani imbalance kelas**: stratify split, tambahkan metrik F1/ROC-AUC, opsi `classWeight`.
10. **Simpan mapping label** (indeks ↔ label) di metadata registry.
11. **Guard** `jumlah_sks_kurikulum` (kosong / multi kurikulum).
12. **Migrasi riwayat prediksi** ke database ringan (SQLite/Postgres) atau rotasi file JSON.

### Low Priority

13. **Incremental / partitioning** pada penulisan Iceberg bila data bertumbuh.
14. **Bersihkan script ad-hoc** (`scripts/cek_*.py`, `check_*.py`) ke folder dev terpisah.
15. **Tambah eksperimen perbandingan model** (Logistic Regression, Decision Tree) untuk memperkuat hasil penelitian.
16. **Analisis feature** (korelasi / feature importance) untuk bab pembahasan.
17. **Sederhanakan komentar blok** `# ====` bila diperlukan.

---

## 17. Kesimpulan

Project **Academic Graduation Prediction System** telah mengimplementasikan arsitektur *data lakehouse* berlapis (Bronze → Silver → Gold → Feature Store) yang diintegrasikan dengan pipeline Machine Learning (Gaussian Naive Bayes) untuk memprediksi tingkat kelulusan mahasiswa — **sesuai dengan judul dan tujuan penelitian**.

**Kekuatan utama:**
- Arsitektur berlapis yang bersih, modular, dan terdokumentasi.
- Pemisahan training/inference dataset yang benar pada Feature Store.
- Pipeline ML standar (preprocessing, CV, evaluasi, registry) dengan metrik lengkap.
- Dashboard web interaktif yang lengkap dan dapat dioperasikan tanpa reload.
- Infrastruktur data lakehouse (MinIO, HMS, Trino, Superset, Airflow) lengkap via Docker.

**Hal yang perlu diperhatikan sebelum bimbingan:**
- Risiko keamanan dasar (sanitasi filename, pesan error, autentikasi) perlu dirapikan sebelum publikasi/deployment.
- Efisiensi runtime (reuse SparkSession, cache model, optimasi batch prediction) perlu dibenahi agar demo di mesin lokal berjalan lancar.
- Aspek eksperimen penelitian (perbandingan model, analisis feature, dokumentasi hasil pada dataset final) perlu dilengkapi untuk mendukung laporan tugas akhir.
- 2 unit test terkait Spark gagal di lingkungan lokal karena keterbatasan konfigurasi Iceberg/Spark — bukan regresi kode, namun perlu dikondisikan agar tidak membingungkan saat penilaian.

Secara keseluruhan, **kualitas project baik dan layak digunakan sebagai dasar laporan tugas akhir**, dengan catatan penyempurnaan yang telah dirinci pada bab temuan dan peningkatan.
