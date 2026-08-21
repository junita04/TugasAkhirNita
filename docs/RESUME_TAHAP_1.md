# Resume Tahap 1 — Penggantian Dataset

> Dokumen ini adalah laporan audit (Stage 1) repository untuk revisi final skripsi
> yang berjudul "Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan
> Model Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis
> Machine Learning".
>
> **Aturan tahap ini:** tidak ada perubahan kode, tidak ada pengecualian — seluruh
> angka di bawah diperoleh langsung dari pembacaan file dataset (pandas) atau
> metadata Iceberg. Bagian yang belum dapat diverifikasi ditandai
> "BELUM TERVERIFIKASI".

## 1. Dataset Lama

- Nama file: `(asli)req_data_rut.xlsx`
- Lokasi: `D:\TA\TugasAkhirNita\Data\(asli)req_data_rut.xlsx`
- Ukuran file: 1.949.705 bytes
- Jumlah baris (per sheet):
  - Referensi Data Mahasiswa : 37.655
  - Data Program Studi       : 44
  - Data Mata Kuliah         : 0 (kosong)
  - Data Kelas               : 3.540
  - Data Kurikulum           : 147
  - Data KHS                 : 28.273
- Jumlah kolom (per sheet):
  - Referensi Data Mahasiswa : 8
  - Data Program Studi       : 3
  - Data Mata Kuliah         : 0
  - Data Kelas               : 3
  - Data Kurikulum           : 2
  - Data KHS                 : 3
- Kolom:
  - Referensi Data Mahasiswa : `ID`, `Jenis Kelamin`, `Tanggal Masuk`, `Tanggal Keluar`, `IPK`, `Total SKS`, `Jumlah MK`, `Status Mahasiswa`
  - Data KHS                 : `ID`, `IP`, `SKS`
- Status file: dipakai sebagai sumber data pipeline saat ini.

## 2. Dataset Baru

- Nama file: `(asli)req_data_rut (1).xlsx`
- Lokasi: `D:\TA\TugasAkhirNita\Data\(asli)req_data_rut (1).xlsx`
- Ukuran file: 2.144.392 bytes
- Jumlah sheet: 6
- Nama sheet yang digunakan:
  1. Referensi Data Mahasiswa
  2. Data Program Studi
  3. Data Mata Kuliah
  4. Data Kelas
  5. Data Kurikulum
  6. Data KHS
- Jumlah baris (per sheet):
  - Referensi Data Mahasiswa : 37.655
  - Data Program Studi       : 44
  - Data Mata Kuliah         : 0 (kosong)
  - Data Kelas               : 3.540
  - Data Kurikulum           : 147
  - Data KHS                 : 28.273
- Jumlah kolom (per sheet):
  - Referensi Data Mahasiswa : 8
  - Data Program Studi       : 3
  - Data Mata Kuliah         : 0
  - Data Kelas               : 3
  - Data Kurikulum           : 2
  - Data KHS                 : 4
- Kolom:
  - Referensi Data Mahasiswa : `ID_MHS`, `Jenis Kelamin`, `Tanggal Masuk`, `Tanggal Keluar`, `IPK`, `Total SKS`, `Jumlah MK`, `Status Mahasiswa`
  - Data KHS                 : `ID_KHS`, `ID_MHS`, `IP`, `SKS`
- Catatan penting: dibandingkan pemeriksaan awal sesi ini, file dataset baru pernah
  berganti isi (ukuran awal 2.486.077 → 2.144.392 bytes). Angka di atas adalah
  kondisi file saat laporan ini ditulis (baca langsung dari disk).

## 3. Perbandingan Dataset

| Komponen | Dataset Lama | Dataset Baru |
|---|---:|---:|
| Jumlah baris Referensi | 37.655 | 37.655 |
| Jumlah baris KHS | 28.273 | 28.273 |
| Jumlah baris Program Studi | 44 | 44 |
| Jumlah baris Kelas | 3.540 | 3.540 |
| Jumlah baris Kurikulum | 147 | 147 |
| Jumlah baris Mata Kuliah | 0 | 0 |
| Jumlah kolom Referensi | 8 | 8 |
| Jumlah kolom KHS | 3 | 4 |
| Kolom id Referensi | `ID` | `ID_MHS` |
| Kolom id KHS | `ID` | `ID_KHS`, `ID_MHS` |
| Kolom IP/SKS KHS | `IP`, `SKS` | `IP`, `SKS` |
| Missing Tanggal Masuk (Referensi) | 4.943 | 4.943 |
| Missing Tanggal Keluar (Referensi) | 20.105 | 20.105 |
| Duplikat baris penuh (Referensi) | 0 | 0 |
| Duplikat baris penuh (KHS) | 0 | 0 |
| Duplikat baris penuh (Data Kelas) | 45 | 45 |
| Perbedaan nilai IP KHS (baris) | — | 6.176 |
| Perbedaan nilai SKS KHS (baris) | — | 0 |
| Perbedaan nilai IPK/Total SKS/Jumlah MK/Status/JK/Tanggal (Referensi) | — | 0 |

Hasil pembandingan antar file (merge by `ID_MHS`):

- Himpunan `ID_MHS` pada Referensi identik (37.655 dari 37.655 cocok, 0 di luar).
- Himpunan `ID_MHS` pada KHS identik (28.273 dari 28.273 cocok, 0 di luar).
- Referensi: tidak ada perbedaan nilai pada kolom `Jenis Kelamin`, `IPK`,
  `Total SKS`, `Jumlah MK`, `Status Mahasiswa`, `Tanggal Masuk`, `Tanggal Keluar`.
- KHS: `SKS` identik; nilai `IP` berbeda pada **6.176 baris** (bukan sekadar
  presisi float — tetap berbeda setelah pembulatan 2 desimal).

## 4. Validasi Dataset

- Apakah file dapat dibaca? **YA** (dibaca berhasil dengan `pandas.read_excel`).
- Apakah seluruh sheet dapat dibaca? **YA** — 6 sheet terbaca; `Data Mata Kuliah`
  kosong (konsisten dengan dataset lama; pipeline meng-skip sheet kosong di Bronze).
- Apakah kolom penting tersedia? **YA dengan catatan** — kolom nilai (IPK, Total SKS,
  Jumlah MK, IP, SKS, status, tanggal) tersedia, tetapi kolom identifier berubah nama:
  - Referensi: `ID` → `ID_MHS`
  - KHS: `ID` → `ID_KHS` + `ID_MHS`
- Apakah terdapat missing value? **YA**:
  - `Tanggal Masuk` 4.943 (sama dengan dataset lama)
  - `Tanggal Keluar` 20.105 (sama dengan dataset lama)
  - Tidak ada missing pada IPK/Total SKS/Jumlah MK/Status/ID/IP/SKS.
- Apakah terdapat duplikasi? Duplikat baris penuh = 0 pada Referensi dan KHS;
  duplikat baris penuh pada Data Kelas = 45 (sama di kedua dataset).
- Apakah tipe data sesuai? **YA** — IPK/IP double, Total SKS/SKS/Jumlah MK int,
  kolom id dan status string; tanggal terbaca sebagai string `YYYY-MM-DD`
  (dikonversi menjadi `date` di Silver).
- Apakah struktur dataset sesuai dengan pipeline yang sudah ada?
  **BELUM SEPENUHNYA SESUAI** — struktur nilai identik, tetapi nama kolom id
  berubah. Pipeline Silver (`backend/silver/silver.py`) memetakan kolom sumber
  `ID` → `id_mahasiswa`; pada dataset baru kolom tersebut bernama `ID_MHS`,
  sehingga pemetaan kolom perlu disesuaikan agar pipeline berjalan.

## 5. Dampak terhadap Pipeline

- File/script yang perlu diubah (potensi, untuk Tahap 2):
  - `backend/silver/silver.py` — SILVER_SPECS untuk `data_referensi_mahasiswa`
    dan `data_khs`: ganti/tambah pemetaan `ID_MHS` → `id_mahasiswa` (dan putuskan
    apakah `ID_KHS` ikut dipakai; saat ini Fact KHS grain 1 baris = 1 mahasiswa).
  - `backend/services/pipeline_entry.py` — `DEFAULT_FILENAME` saat ini
    `req_data_rut.xlsx` yang TIDAK ADA di folder `data/`; perlu disesuaikan atau
    dataset baru disalin dengan nama tersebut agar resolusi file berhasil.
  - `scripts/run_pipeline.py` — argumen default mengikuti `DEFAULT_FILENAME`.
  - `docker/airflow/dags/prediction_pipeline.py` — memanggil
    `resolve_pipeline_file("req_data_rut.xlsx")`, mengikuti `DEFAULT_FILENAME`.
  - Dokumen/README bila menyebut nama file sumber.
- File/script yang TIDAK perlu diubah (perkiraan, diverifikasi di Tahap 2):
  - `backend/bronze/bronze.py` — membaca berdasarkan nama sheet (tidak berubah)
    dan menyimpan raw; nama tabel bronze tidak berubah.
  - `backend/gold/*` — membaca dari Silver dengan nama kolom target yang sudah
    dibakukan (`id_mahasiswa`, `ip`, `sks`, dst.), bukan nama kolom Excel.
  - `backend/feature_store/*` — membaca dari Gold, nama kolom target tidak berubah.
  - `backend/ml/*` — membaca Feature Store (`training_dataset`, `inference_dataset`),
    nama kolom tidak berubah.
  - `backend/spark/session.py`, `backend/config/settings.py` — tidak terkait data.
- Apakah struktur Bronze → Silver → Gold tetap kompatibel?
  **KONDISIONAL** — tetap kompatibel selama pemetaan kolom id di Silver
  disesuaikan dengan nama kolom baru (`ID_MHS`); tanpa penyesuaian, kolom
  `id_mahasiswa` tidak akan terbentuk.
- Apakah Feature Store tetap kompatibel? **YA** — membaca Gold
  (`gold.dim_mahasiswa`, `gold.fact_khs`) yang kolomnya sudah distandarkan.
- Apakah pipeline Machine Learning tetap kompatibel? **YA** — membaca
  `feature_store.training_dataset` dan `feature_store.inference_dataset`
  (kolom: `id_mahasiswa`, `ip`, `sks`, `angkatan`, `jumlah_mk`); tidak membaca
  file Excel secara langsung.
- Apakah Superset perlu diperbarui? **YA/TIDAK tergantung sumber** — Superset
  membaca via Trino dari `iceberg.gold.*` dan `iceberg.feature_store.prediction_result*`.
  Jika tabel Gold/Feature Store tetap bernama sama, dataset Superset tidak perlu
  diubah. Perubahan hanya diperlukan bila nama tabel/schema diubah.
- Dampak nilai: karena IP KHS berbeda pada 6.176 baris, maka `training_dataset`
  (13.347 baris) dan seluruh hasil training/inference akan berubah setelah
  pipeline dijalankan ulang dengan dataset baru.

## 6. File yang Diubah

Pada Tahap 1 (audit) **tidak ada file yang diubah**. Daftar di bawah adalah
perubahan yang **direncanakan** untuk Tahap 2 (belum dieksekusi).

| File | Perubahan | Alasan |
|---|---|---|
| `backend/silver/silver.py` | Pemetaan kolom id `ID_MHS` (Referensi & KHS) | Nama kolom id berubah di dataset baru |
| `backend/services/pipeline_entry.py` | Sesuaikan `DEFAULT_FILENAME` | File `req_data_rut.xlsx` tidak ada di `data/` |
| `scripts/run_pipeline.py` | (opsional) nama default | Mengikuti `DEFAULT_FILENAME` |
| `docker/airflow/dags/prediction_pipeline.py` | (opsional) nama file pipeline | Mengikuti `DEFAULT_FILENAME` |

## 7. File/Data yang Dihasilkan

Tahap 1 hanya audit (baca). Tidak ada file/baris data baru yang dibuat. Artefak yang
diidentifikasi sebagai dasar Tahap 2:

- Dataset baru: `Data\(asli)req_data_rut (1).xlsx`
- Hasil pengukuran waktu (eksisting, tidak dijalankan ulang):
  `results/measure_training.py`, `results/measure_inference.py`,
  `results/timing_summary.csv`, `results/training_timing.csv`,
  `results/inference_timing.csv`, `results/REPORT_BAB4.md`
- Quality report eksisting: `logs/data_quality_report.json`,
  `logs/feature_store_quality_report.json`,
  `logs/inference_quality_report.json`,
  `logs/inference_iceberg_quality_report.json`
- Prediksi eksisting: `Data/predictions/*.parquet`

## 8. Validasi Akhir

- Dataset baru berhasil dibaca: **YA**
- Pipeline dapat menggunakan dataset baru: **YA, SETELAH penyesuaian pemetaan
  kolom id di Silver (Tahap 2)** — tanpa penyesuaian, `id_mahasiswa` tidak terbentuk.
- Tidak ada error kritis: **YA** (pada tahap audit; belum ada eksekusi pipeline)
- Data siap untuk Tahap 2: **YA** (dengan catatan penyesuaian kolom id)

## 9. Kesimpulan

Tahap 1 (audit) **selesai**. Dataset baru ditemukan, terbaca, dan nilai datanya
terverifikasi hampir identik dengan dataset lama (perbedaan signifikan: nama kolom
id `ID` → `ID_MHS`/`ID_KHS` dan nilai IP KHS berbeda pada 6.176 baris). Pipeline
(Bronze → Silver → Gold → Feature Store → ML) tetap kompatibel secara struktur
karena bergantung pada nama kolom target yang dibakukan, tetapi **Silver perlu
penyesuaian pemetaan kolom id** sebelum pipeline dijalankan ulang dengan dataset
baru. Aman untuk melanjutkan ke Tahap 2 selama penyesuaian tersebut dijadwalkan
sebagai langkah pertama.
