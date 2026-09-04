# Export Data _barulagi - Laporan

## Sumber Data

- **File Excel**: `(asli)req_data_rut (baru).xlsx`
- **Lokasi di container**: `/opt/airflow/data/req_data_rut_baru.xlsx`
- **Tanggal export**: 2026-09-02

## Pipeline

Bronze → Silver → Gold → Feature Store → Training Dataset → Inference Dataset

Semua proses menggunakan logic yang sama dengan pipeline utama. Tidak ada perubahan logic, mapping, feature engineering, label, atau pembagian training/inference.

## Jumlah Data per Layer

### Bronze

| File | Jumlah Baris | Jumlah Kolom |
|------|-------------|--------------|
| bronze_data_referensi_mahasiswa_barulagi.xlsx | 37,655 | 8 |
| bronze_data_khs_barulagi.xlsx | 28,273 | 4 |
| bronze_data_program_studi_barulagi.xlsx | 44 | 3 |
| bronze_data_kelas_barulagi.xlsx | 3,540 | 3 |
| bronze_data_kurikulum_barulagi.xlsx | 147 | 2 |

### Silver

| File | Jumlah Baris | Jumlah Kolom |
|------|-------------|--------------|
| silver_silver_mahasiswa_barulagi.xlsx | 32,703 | 8 |
| silver_silver_khs_barulagi.xlsx | 27,843 | 4 |
| silver_silver_program_studi_barulagi.xlsx | 44 | 3 |
| silver_silver_kelas_barulagi.xlsx | 3,540 | 3 |
| silver_silver_kurikulum_barulagi.xlsx | 147 | 2 |

**Catatan Silver**: 4,952 baris dari Bronze dihapus (4,943 NULL tanggal_masuk + 9 invalid dates).

### Gold

| File | Jumlah Baris | Jumlah Kolom |
|------|-------------|--------------|
| gold_dim_mahasiswa_barulagi.xlsx | 32,703 | 18 |
| gold_fact_khs_barulagi.xlsx | 27,843 | 4 |
| gold_model_metrics_final_barulagi.xlsx | 2 | 16 |
| gold_confusion_matrix_final_barulagi.xlsx | 8 | 4 |
| gold_classification_report_final_barulagi.xlsx | 6 | 6 |
| gold_prediction_by_angkatan_final_barulagi.xlsx | 3 | 4 |
| gold_model_predictions_barulagi.xlsx | 12,244 | 11 |

### Feature Store

| File | Jumlah Baris |
|------|-------------|
| feature_store_training_barulagi.xlsx | 15,599 |
| feature_store_inference_barulagi.xlsx | 12,244 |

### Training Dataset

| File | Jumlah Baris | Jumlah Kolom |
|------|-------------|--------------|
| training_8_features_barulagi.xlsx | 15,599 | 10 |

Kolom: `id_mahasiswa, jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks, label`

### Inference Dataset

| File | Jumlah Baris | Jumlah Kolom |
|------|-------------|--------------|
| inference_2022_2024_barulagi.xlsx | 12,244 | 9 |

Kolom: `id_mahasiswa, jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks`

## 8 Fitur yang Digunakan

| No | Fitur | Deskripsi |
|----|-------|-----------|
| 1 | jk_enc | Jenis kelamin (0=Perempuan, 1=Laki-laki) |
| 2 | angkatan | Tahun masuk |
| 3 | ip | Indeks Prestasi semester terakhir |
| 4 | ipk | Indeks Prestasi Kumulatif |
| 5 | total_sks | Total SKS yang telah ditempuh |
| 6 | jumlah_mk | Jumlah mata kuliah yang telah diambil |
| 7 | sks_seharusnya | Target SKS berdasarkan semester |
| 8 | selisih_sks | total_sks - sks_seharusnya |

## Distribusi Label Training

| Label | Jumlah | Persentase |
|-------|--------|-----------|
| 0 (Tepat Waktu) | 3,153 | 20.21% |
| 1 (Terlambat) | 12,446 | 79.79% |
| **Total** | **15,599** | **100%** |

## Distribusi Angkatan Inference

| Angkatan | Jumlah | Persentase |
|----------|--------|-----------|
| 2022 | 3,987 | 32.56% |
| 2032 | 3,985 | 32.55% |
| 2024 | 4,272 | 34.89% |
| **Total** | **12,244** | **100%** |

## Validasi

- [x] Semua file berhasil dibuat
- [x] Semua file berada di folder `data/`
- [x] Semua file menggunakan suffix `_barulagi.xlsx`
- [x] Jumlah baris antar-layer dapat dilacak
- [x] Tidak ada data inference yang masuk training (overlap = 0)
- [x] 8 fitur tetap identik dengan baseline
- [x] Logic SKS tetap identik dengan sistem yang sudah ada (TARGET_SKS: {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144})
- [x] Tidak ada perubahan logic hanya karena proses dijalankan tanpa Airflow
- [x] Label logic tetap: LULUS + <=4 tahun = 0 (TW), LULUS + >4 tahun = 1 (TL), AKTIF 2019-2021 = 1 (TL)
- [x] IP NULL dikeluarkan dari training dan inference (tidak ada imputasi)
- [x] Snapshot semester: 2022→7 (135 SKS), 2023→5 (95 SKS), 2024→3 (55 SKS)

## Daftar File Excel

```
data/bronze_data_referensi_mahasiswa_barulagi.xlsx   (1,350.0 KB)
data/bronze_data_khs_barulagi.xlsx                    (641.4 KB)
data/bronze_data_program_studi_barulagi.xlsx          (6.0 KB)
data/bronze_data_kelas_barulagi.xlsx                  (70.1 KB)
data/bronze_data_kurikulum_barulagi.xlsx              (6.7 KB)
data/silver_silver_mahasiswa_barulagi.xlsx            (1,187.7 KB)
data/silver_silver_khs_barulagi.xlsx                  (644.4 KB)
data/silver_silver_program_studi_barulagi.xlsx        (6.0 KB)
data/silver_silver_kelas_barulagi.xlsx                (70.1 KB)
data/silver_silver_kurikulum_barulagi.xlsx            (6.7 KB)
data/gold_dim_mahasiswa_barulagi.xlsx                 (2,384.1 KB)
data/gold_fact_khs_barulagi.xlsx                      (616.1 KB)
data/gold_model_metrics_final_barulagi.xlsx           (5.5 KB)
data/gold_confusion_matrix_final_barulagi.xlsx        (5.1 KB)
data/gold_classification_report_final_barulagi.xlsx   (5.2 KB)
data/gold_prediction_by_angkatan_final_barulagi.xlsx  (4.9 KB)
data/gold_model_predictions_barulagi.xlsx             (130.6 KB)
data/feature_store_training_barulagi.xlsx             (633.4 KB)
data/feature_store_inference_barulagi.xlsx            (484.6 KB)
data/training_8_features_barulagi.xlsx                (633.4 KB)
data/inference_2022_2024_barulagi.xlsx                (484.6 KB)
```

**Total: 21 file Excel**

## Mapping SKS ITERA (TIDAK BERUBAH)

| Semester | Target SKS |
|----------|------------|
| 1 | 17 |
| 2 | 36 |
| 3 | 55 |
| 4 | 75 |
| 5 | 95 |
| 6 | 115 |
| 7 | 135 |
| 8 | 144 |

## Catatan Penting

1. **Training** berisi mahasiswa LULUS + AKTIF 2019-2021 yang sudah berlabel (0/1).
2. **Inference** berisi mahasiswa AKTIF angkatan 2022, 2023, 2024 tanpa label.
3. **Tidak ada overlap** antara training dan inference.
4. **IP NULL** dikeluarkan dari training (173 baris) dan inference (257 baris).
5. **Gender encoding**: P/PEREMPUAN→0, L/LAKI-LAKI→1, unknown→NULL.
6. **Selisih SKS interpretation**: <-10 = sangat tertinggal, -10..0 = di bawah target, >=0 = memenuhi target.
7. File siap digunakan untuk pemodelan di Google Colab.
