# Laporan Pengukuran Waktu Training & Inference — Bab 4

Tanggal pengukuran : 2026-08-14
File pengukuran     : `results/measure_training.py`, `results/measure_inference.py`
Hasil mentah        : `results/training_timing.csv`, `results/inference_timing.csv`, `results/timing_summary.csv`

---

## 1. Dataset yang Digunakan

| Dataset | Tabel Iceberg | Sumber baca | Baris | Fitur |
|---|---|---|---|---|
| Training | `feature_store.training_dataset` | parquet aktif (current snapshot), eager via pyarrow | **13.347** | `ip`, `sks`, `angkatan`, `jumlah_mk` |
| Inference | `feature_store.inference_dataset` | parquet aktif (current snapshot), eager via pyarrow | **14.926** | `ip`, `sks`, `angkatan`, `jumlah_mk` |

Distribusi target training: `Tepat Waktu` = 3.211, `Terlambat` = 10.136 (imbalance ~24% : 76%).

> Dataset TIDAK diubah. Dibaca langsung dari parquet aktif Iceberg yang identik
> dengan yang dibaca `spark.table(...)`. Tidak ada penulisan ulang ke Iceberg.

## 2. Model dan Versi

| Varian | Model | Artifact |
|---|---|---|
| MODEL A (without_smote) | `GaussianNB()` | `models/gaussian_nb_v2/without_smote/model.joblib` |
| MODEL B (with_smote) | `ImbPipeline([SMOTE, GaussianNB])` | `models/gaussian_nb_v2/with_smote/model.joblib` |

- Nama model : `gaussian_nb_lulusan`, versi **v2.0.0** (revisi Tahap 5, **tanpa StandardScaler**, `preprocessing=[]`).
- Class mapping : `Tepat Waktu -> 0`, `Terlambat -> 1`.
- Parameter : `random_state=42`, fitur 4.

## 3. Konfigurasi Runtime

- Spark **TIDAK digunakan pada wilayah pengukuran**. Dataset dibaca dengan
  `pyarrow.read_table` (eager) dari parquet aktif tabel Iceberg lokal.
- Training & inference dijalankan dengan **sklearn / imblearn pada numpy
  (eager)** — operasi fit/predict langsung mengeksekusi komputasi numerik,
  bukan membentuk execution plan.
- Interpreter : `D:\TA\TugasAkhirNita\.venv\Scripts\python.exe`
  (sklearn 1.9.0, imblearn 0.14.2, pyarrow, pandas, numpy).
- Environment produksi (`SPARK_MODE=local`, `ICEBERG_CATALOG=local`,
  `ICEBERG_WAREHOUSE=file:///D:/TA/TugasAkhirNita/iceberg`) hanya untuk
  menyediakan data/model; tidak dieksekusi pada pengukuran.

## 4. Metode Pengukuran

- Timer : `time.perf_counter()`.
- **Warm-up** : 1× run setiap skenario dilakukan SEBELUM statistik dan TIDAK
  dihitung (menghindari overhead inisialisasi numpy/sklearn pertama).
- **Jumlah run pengukuran** : 5× per skenario.
- Statistik : mean, median, min, max, std.
- **Bukti eksekusi nyata (bukan lazy)**:
  - Training tanpa SMOTE : dicek `class_count_` hasil fit == distribusi data
    (`[3211, 10136]`). PASS.
  - SMOTE : dicek jumlah baris setelah resample == **20.272** dan kelas
    seimbang (`[10136, 10136]`). PASS.
  - Inference : prediksi script **dibandingkan id-per-id** dengan hasil prediksi
    produksi `data/predictions/prediction_result_{variant}.parquet` →
    agreement **100,00%** untuk kedua varian. Ini membuktikan expression
    prediction/probability benar-benar dievaluasi pada seluruh baris.

### Penjelasan tentang lazy evaluation Spark

Pipeline produksi (ETL/feature store) memakai Spark yang bersifat lazy.
Namun script pengukuran ini **tidak memanggil Spark sama sekali**; data
dibaca eager dan fit/predict dijalankan pada numpy. Oleh karena itu hasil
berikut adalah **waktu komputasi aktual di memori**, bukan waktu pembuatan
execution plan. Bila ingin mengukur jalur penuh produksi (termasuk
`spark.table(...).toPandas()` + tulis Iceberg), gunakan DAG Airflow
`prediction_pipeline` — di luar lingkup pengukuran ini.

## 5. Hasil Training (5 run, warm-up dikecualikan)

| Skenario | Baris | mean (s) | median (s) | min (s) | max (s) | std (s) |
|---|---|---|---|---|---|---|
| Tanpa SMOTE — `fit` GaussianNB | 13.347 | **0.001303** | 0.001273 | 0.001242 | 0.001418 | 0.000074 |
| Dengan SMOTE — `SMOTE.fit_resample` | 13.347→20.272 | **0.012490** | 0.012751 | 0.011487 | 0.013145 | 0.000666 |
| Dengan SMOTE — `fit` GaussianNB (data hasil SMOTE) | 20.272 | **0.001802** | 0.001738 | 0.001709 | 0.001923 | 0.000105 |
| Dengan SMOTE — TOTAL pipeline `fit` | 13.347→20.272 | **0.012881** | 0.012841 | 0.012550 | 0.013296 | 0.000271 |

Catatan:
- `fit_total` ≈ `smote_fit_resample` + `gnb_fit_after_smote` (komponen saling
  konsisten).
- SMOTE menyumbang ~97% dari waktu training dengan SMOTE (resampling dengan
  tetangga terdekat jauh lebih mahal daripada fit GaussianNB).

## 6. Hasil Inference (5 run, warm-up dikecualikan)

| Varian | Komponen | Baris | mean (s) | median (s) | min (s) | max (s) | std (s) |
|---|---|---|---|---|---|---|---|
| without_smote | input preparation | 14.926 | 0.000402 | 0.000298 | 0.000272 | 0.000718 | 0.000186 |
| without_smote | model load (joblib) | 14.926 | 0.000301 | 0.000267 | 0.000254 | 0.000432 | 0.000074 |
| without_smote | **predict** | 14.926 | **0.000465** | 0.000449 | 0.000417 | 0.000561 | 0.000056 |
| without_smote | predict_proba | 14.926 | 0.000928 | 0.000913 | 0.000886 | 0.001010 | 0.000048 |
| without_smote | **end-to-end** | 14.926 | **0.002130** | 0.002043 | 0.001942 | 0.002444 | 0.000209 |
| with_smote | input preparation | 14.926 | 0.000355 | 0.000275 | 0.000229 | 0.000630 | 0.000170 |
| with_smote | model load (joblib) | 14.926 | 0.000556 | 0.000523 | 0.000510 | 0.000670 | 0.000067 |
| with_smote | **predict** | 14.926 | **0.000502** | 0.000467 | 0.000451 | 0.000631 | 0.000074 |
| with_smote | predict_proba | 14.926 | 0.001002 | 0.001018 | 0.000964 | 0.001030 | 0.000033 |
| with_smote | **end-to-end** | 14.926 | **0.002539** | 0.002558 | 0.002386 | 0.002677 | 0.000108 |

Keterangan komponen:
- `input_preparation` : `pdf[fitur].astype(float).to_numpy()`.
- `model_load` : `load_model()` = `joblib.load(model.joblib)` + baca metadata.
- `predict` : `pipeline.predict(X)` → label kelas.
- `predict_proba` : `pipeline.predict_proba(X)` → probabilitas tiap kelas.
- `end_to_end` : input prep + model load + predict + predict_proba dalam satu
  stopwatch (tanpa baca parquet dari disk).

## 7. Throughput

Berbasis mean `predict` (in-memory numpy):

| Varian | rows/detik | per-row |
|---|---|---|
| without_smote | 32.087.884 | ~31,2 ns/baris |
| with_smote | 29.716.493 | ~33,7 ns/baris |

> Throughput ini hanya sah untuk komputasi prediksi di memori (batch numpy),
> BUKAN end-to-end produksi (tidak termasuk baca parquet, Spark, maupun
> penulisan hasil). End-to-end inference ≈ 2,1–2,5 ms.

## 8. Kesimpulan Kelayakan untuk Bab 4

- **Layak digunakan** untuk menyatakan waktu komputasi model (fit/predict)
  di memori. Angka valid dibuktikan dengan:
  1) validasi `class_count_` / jumlah baris setelah SMOTE (20.272);
  2) **100% agreement** prediksi dengan hasil produksi.
- Angka yang tampak "terlalu cepat" adalah realistis karena:
  - data kecil (13.347 / 14.926 baris × 4 fitur);
  - GaussianNB adalah estimasi parametrik sederhana (hitung rata-rata &
    varians per kelas) — sangat cepat di numpy;
  - pengukuran hanya komputasi murni, tanpa I/O disk maupun Spark.
- **Batasan**: hasil TIDAK mencakup waktu baca dataset, startup Spark, dan
  penulisan hasil ke Iceberg (jalur produksi). Untuk angka end-to-end sistem
  penuh, gunakan log DAG Airflow (`prediction_pipeline`) atau ukur
  `inference.py` secara utuh termasuk `spark.table().toPandas()`.

## 9. Reproduksi

```powershell
cd D:\TA\TugasAkhirNita
.\.venv\Scripts\python.exe results\measure_training.py
.\.venv\Scripts\python.exe results\measure_inference.py
```

Output:
- `results/training_timing.csv` — per-run training
- `results/inference_timing.csv` — per-run inference
- `results/timing_summary.csv` — ringkasan gabungan (training + inference)
- `results/training_timing_meta.json`, `results/inference_timing_meta.json`
