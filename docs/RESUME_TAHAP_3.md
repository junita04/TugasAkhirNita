# Resume Tahap 3 — Feature Store + Machine Learning (Dataset Baru)

> Dokumen ini adalah laporan eksekusi (Stage 3) pembangunan kembali Feature Store
> dan pipeline Machine Learning untuk revisi final skripsi
> "Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model
> Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis
> Machine Learning".
>
> **Aturan tahap ini:** Feature Store WAJIB dibangun dari Gold Layer dataset baru
> (Tahap 2), bukan dari Excel. Bronze/Silver/Gold tidak diulang. Tidak ada
> target leakage. SMOTE hanya pada data training. Model utama tetap GaussianNB.
> Model lama (v1.0.0, v2.0.0) tidak dihapus; dibuat versi baru v3.0.0.

## 1. Tujuan Tahap 3

Membangun kembali Feature Store dan pipeline Machine Learning berdasarkan Gold
Layer dataset baru, menghasilkan model prediksi kelulusan yang siap inference,
serta mengukur waktu training & inference untuk kebutuhan Bab 4.

Alur yang dijalankan:
`Gold Layer → Feature Engineering → Feature Store → Training (2 varian) →
Evaluasi → Model Registry (v3.0.0) → Inference → hasil prediksi`.

## 2. Sumber Data

- Input Feature Store: **Gold Layer** tabel Iceberg dari Tahap 2:
  - `local.gold.dim_mahasiswa` (32.703 baris)
  - `local.gold.fact_khs` (28.273 baris)
- **Tidak membaca file Excel** untuk proses ML. Data Excel hanya sampai Bronze.
- Verifikasi Gold: `gold.gold_mahasiswa_fakta` (32.703 baris, JOIN duplicate=0,
  NULL ID=0) sudah dibuat di Tahap 2 dan tidak diubah.

## 3. Feature Engineering

Turunan fitur (tetap, sesuai penelitian):
- `angkatan` = tahun `tanggal_masuk`
- `lama_studi` = `tanggal_keluar - tanggal_masuk` (HANYA untuk membentuk label
  training, tidak pernah menjadi fitur X)

Fitur X (4 fitur, tanpa perubahan dari penelitian):
`ip`, `sks`, `angkatan`, `jumlah_mk`

Label/target: `status_kelulusan` → `Tepat Waktu` (lama_studi ≤ 4 tahun / 1460
hari) vs `Terlambat` (> 4 tahun). Label hanya dibentuk untuk mahasiswa LULUS.

Pemeriksaan leakage otomatis:
- `FORBIDDEN_FEATURES` = jenis_kelamin, tanggal_masuk, tanggal_keluar, ipk,
  total_sks, status_mahasiswa, lama_studi, status_kelulusan, estimasi_semester,
  persentase_sks.
- Hasil: **forbidden=[]**, **extra=[]** (0 fitur terlarang pada training &
  inference dataset).

## 4. Feature Store (dibuat dari Gold baru)

Tabel yang dibuat/diperbarui (Iceberg `local.feature_store.*`):

| Tabel | Baris | Kolom |
|---|---|---:|---|
| `feature_store.training_dataset` | **13.347** | id_mahasiswa, ip, sks, angkatan, jumlah_mk, status_kelulusan |
| `feature_store.inference_dataset` | **14.926** | id_mahasiswa, ip, sks, angkatan, jumlah_mk |

Validasi Feature Store (`logs/feature_store_quality_report.json`):
- JOIN: total 32.703 = distinct 32.703, duplicate 0, row multiplication 0.
- Training: jumlah awal LULUS 13.347, valid 13.347, tanpa KHS 0, duplicate id 0,
  null fitur 0.
- Inference: jumlah awal AKTIF 14.926, valid 14.926, tanpa KHS 0, duplicate id 0,
  null fitur 0.
- Leakage: forbidden=[] extra=[] untuk keduanya.

Distribusi target training: `Tepat Waktu` = 3.211, `Terlambat` = 10.136
(imbalance ≈ 24% : 76%).

> Catatan: jumlah baris sama dengan dataset lama karena himpunan ID_MHS identik;
> yang berubah adalah nilai `ip` KHS pada 6.176 baris (hasil audit Tahap 1).
> Data parquet aktif yang dibaca adalah snapshot terbaru (dibuktikan 100%
> agreement inference dengan hasil produksi).

## 5. Machine Learning — Konfigurasi

- Model utama (tetap): **Gaussian Naive Bayes** (`sklearn.naive_bayes.GaussianNB`)
- Skenario:
  - **A. Tanpa SMOTE**: `GaussianNB()`
  - **B. Dengan SMOTE**: `ImbPipeline([SMOTE(random_state=42), GaussianNB()])`
- Parameter: `random_state=42`, tanpa StandardScaler (`preprocessing=[]`).
- Pembagian data (tetap sesuai penelitian):
  - `train_test_split(test_size=0.20, random_state=42, stratify=y)`
  - Development 80% (10.677 baris), holdout test 20% (2.670 baris).
  - `StratifiedKFold(k=10, shuffle=True, random_state=42)` pada data development.
- SMOTE **hanya** diterapkan pada data training (di dalam pipeline cross-fold);
  test set tidak di-SMOTE.

Sebelum training (ringkas):
- Jumlah baris: 13.347
- Jumlah fitur: 4
- Fitur: ip, sks, angkatan, jumlah_mk
- Missing value: 0
- Distribusi target: {Tepat Waktu: 3.211, Terlambat: 10.136}
- Data masuk training (development): 10.677

## 6. Hasil Evaluasi

Holdout test (20%, positive = "Tepat Waktu"):

| Metrik | Tanpa SMOTE | Dengan SMOTE |
|---|---:|---:|
| Accuracy | **0.7378** | 0.7165 |
| Precision | **0.3407** | 0.3304 |
| Recall | 0.0966 | **0.1745** |
| F1-score | 0.1505 | **0.2283** |

Confusion Matrix (rows=actual, cols=predicted; 0=Tepat Waktu, 1=Terlambat):
- Tanpa SMOTE: `[[62, 580], [120, 1908]]`
- Dengan SMOTE: `[[112, 530], [227, 1801]]`

CV 10-fold (mean):

| Metrik | Tanpa SMOTE | Dengan SMOTE |
|---|---:|---:|
| Accuracy | 0.7413 | 0.7256 |
| Precision | 0.3617 | 0.3638 |
| Recall | 0.1028 | 0.1872 |
| F1-score | 0.1592 | 0.2464 |

Pola: SMOTE meningkatkan recall/F1 untuk kelas minoritas Tepat Waktu, tetapi
menurunkan accuracy. Konsisten dengan literatur SMOTE untuk data imbalance.

## 7. Model Registry / Versioning

- Versi baru dibuat: **v3.0.0** (dataset revisi final), model name
  `gaussian_nb_lulusan`, **tanpa** StandardScaler.
- Artifact:
  - `models/gaussian_nb_v3/without_smote/model.joblib` + `metadata.json`
  - `models/gaussian_nb_v3/with_smote/model.joblib` + `metadata.json`
- Model lama **tidak dihapus**: `models/gaussian_nb` (v1) dan
  `models/gaussian_nb_v2` (v2.0.0) tetap utuh.
- Metadata mencatat: feature_names, class_mapping, class_distribution,
  training_row_count, cv_summary, holdout, has_scaler=False, artifact_path.
- **Versi yang dipakai untuk inference: v3.0.0** (tertulis pada kolom
  `model_version` di setiap baris hasil prediksi).

## 8. Inference

- Input: `feature_store.inference_dataset` (14.926 mahasiswa AKTIF).
- Validasi schema input: total 14.926 = distinct id 14.926, null feature 0,
  duplicate id 0, feature count 4.
- Model v3.0.0 (tanpa SMOTE & dengan SMOTE) memprediksi 14.926 baris masing-masing.
- Output per varian (Parquet biasa): `data/predictions/prediction_result_*.parquet`
  lalu dipublish ke Iceberg `local.feature_store.prediction_result_*`.
- Kolom hasil: `id_mahasiswa, ip, sks, angkatan, jumlah_mk,
  prediksi_status_kelulusan, probabilitas_prediksi, prediction_timestamp,
  model_version, model_variant`.
- Distribusi prediksi (14.926):
  - Tanpa SMOTE: Tepat Waktu 10.370, Terlambat 4.556
  - Dengan SMOTE: Tepat Waktu 11.145, Terlambat 3.781
- Perbandingan model: agreement 14.147 / 14.926 (94,78%), disagreement 779
  (5,22%).

Quality gate output (kedua varian): row_count_ok=TRUE, unique_id_ok=TRUE,
null_ok=TRUE, coverage_ok=TRUE, legacy_schema_ok=TRUE.

Iceberg output (`logs/inference_iceberg_quality_report.json`): SUCCESS untuk
`prediction_result_without_smote`, `prediction_result_with_smote`,
`prediction_comparison` (masing-masing 14.926 baris).

## 9. Pengukuran Waktu (Bab 4)

Metodologi: data dibaca EAGER dari parquet aktif Iceberg (tanpa Spark pada
wilayah pengukuran), warm-up 1× di luar statistik, **5× run** per skenario,
timer `time.perf_counter()`. Statistik: mean / median / min / max / std.
Validasi eksekusi nyata: class_count_ cocok, jumlah baris setelah SMOTE = 20.272
seimbang, dan inference **100% agreement** dengan hasil produksi.

### Training time (mean; 5 run)

| Skenario | Baris | mean (s) | min (s) | max (s) | std (s) |
|---|---:|---:|---:|---:|---:|
| Tanpa SMOTE — fit GaussianNB | 13.347 | **0.001261** | 0.001161 | 0.001319 | 0.000065 |
| Dengan SMOTE — SMOTE.fit_resample | 13.347→20.272 | 0.011138 | 0.010850 | 0.011406 | 0.000210 |
| Dengan SMOTE — fit GNB (hasil SMOTE) | 20.272 | 0.001875 | 0.001818 | 0.002004 | 0.000075 |
| Dengan SMOTE — TOTAL pipeline fit | 13.347→20.272 | **0.013036** | 0.012941 | 0.013122 | 0.000081 |

### Inference time (mean; 5 run, 14.926 baris)

| Varian | Komponen | mean (s) | min (s) | max (s) | std (s) |
|---|---|---:|---:|---:|---:|
| without_smote | input_preparation | 0.000473 | 0.000324 | 0.000810 | 0.000195 |
| without_smote | model_load (joblib) | 0.000324 | 0.000272 | 0.000437 | 0.000066 |
| without_smote | **predict** | **0.000461** | 0.000413 | 0.000553 | 0.000057 |
| without_smote | predict_proba | 0.000904 | 0.000863 | 0.000973 | 0.000046 |
| without_smote | **end_to_end** | **0.002123** | 0.001976 | 0.002381 | 0.000173 |
| with_smote | input_preparation | 0.000421 | 0.000271 | 0.000753 | 0.000206 |
| with_smote | model_load (joblib) | 0.001169 | 0.000598 | 0.002561 | 0.000801 |
| with_smote | **predict** | **0.000625** | 0.000543 | 0.000827 | 0.000116 |
| with_smote | predict_proba | 0.001141 | 0.000919 | 0.001427 | 0.000220 |
| with_smote | **end_to_end** | **0.002715** | 0.002409 | 0.003204 | 0.000341 |

Throughput (mean predict, in-memory numpy): without_smote 32.390.087 baris/detik,
with_smote 23.893.834 baris/detik.

> Waktu tidak mencampur startup Spark/penulisan Iceberg; hanya komputasi model
> (sesuai metodologi penelitian).

## 10. Lokasi Output

- Feature Store (Iceberg): `local.feature_store.training_dataset`,
  `local.feature_store.inference_dataset`
- Evaluasi: `results/evaluation_results.csv` (2 varian)
- Timing per-run: `results/training_timing.csv`, `results/inference_timing.csv`
- Ringkasan timing: `results/timing_summary.csv`
- Metadata timing: `results/training_timing_meta.json`,
  `results/inference_timing_meta.json`
- Prediction gabungan: `results/prediction_result.csv` (14.926 baris, berisi
  id_mahasiswa, angkatan, prediksi & probabilitas kedua varian, versi model)
- Prediction per varian (Parquet): `data/predictions/prediction_result_without_smote.parquet`,
  `data/predictions/prediction_result_with_smote.parquet`,
  `data/predictions/prediction_comparison.parquet`
- Prediction (Iceberg): `local.feature_store.prediction_result_without_smote`,
  `local.feature_store.prediction_result_with_smote`,
  `local.feature_store.prediction_comparison`
- Model: `models/gaussian_nb_v3/` (without_smote & with_smote)
- Quality report: `logs/feature_store_quality_report.json`,
  `logs/inference_quality_report.json`,
  `logs/inference_iceberg_quality_report.json`

## 11. Validasi

| Item | Status |
|---|---|
| Feature Store berasal dari dataset baru (Gold Tahap 2) | **PASS** |
| Tidak ada target leakage (forbidden=[] extra=[]) | **PASS** |
| Jumlah data benar (training 13.347, inference 14.926) | **PASS** |
| Target hanya sebagai label (tidak masuk X) | **PASS** |
| SMOTE hanya pada training (bukan test set) | **PASS** |
| Model berhasil training (GaussianNB, 2 varian) | **PASS** |
| Model berhasil inference (14.926 prediksi/varian) | **PASS** |
| Output prediction tidak kosong | **PASS** |
| Jumlah prediction = jumlah input inference (14.926 = 14.926) | **PASS** |
| Model registry/versioning berhasil (v3.0.0, v1/v2 tidak dihapus) | **PASS** |
| File hasil pengukuran berhasil dibuat (5 file CSV/JSON) | **PASS** |
| Bron­ze/Silver/Gold tidak diulang; snapshot lama tidak dihapus | **PASS** |

## 12. Kesimpulan

Tahap 3 **selesai**. Feature Store dibangun dari Gold Layer dataset baru,
GaussianNB dilatih dalam 2 skenario (tanpa/dengan SMOTE), dievaluasi, versi
model v3.0.0 diregistrasi tanpa menghapus model lama, inference dijalankan untuk
14.926 mahasiswa AKTIF dengan hasil lengkap (ID, prediksi, probabilitas,
angkatan), waktu training & inference diukur 5× run dengan statistik lengkap,
dan seluruh output tersimpan di Iceberg + `results/`. Aman untuk melanjutkan ke
Tahap 4 (visualisasi/dashboard Superset atau penulisan Bab 4).

## 13. Perubahan Kode

- `backend/ml/registry.py` — `MODEL_VERSION` → `v3.0.0`, `ARTIFACT_DIR` →
  `models/gaussian_nb_v3` (v1/v2 tidak disentuh).
- `backend/ml/train.py`, `backend/ml/evaluate.py`, `backend/ml/inference.py` —
  label teks versi/tahap disesuaikan ke "Tahap 3 / v3.0.0" (tanpa mengubah
  logika).
- `results/iceberg_reader.py` — `load_active_parquet` diperbaiki agar memilih
  file parquet milik snapshot AKTIF (mtime terbaru) bila ada beberapa file
  dengan jumlah baris identik (mencegah membaca data lama yang kebetulan punya
  count sama).