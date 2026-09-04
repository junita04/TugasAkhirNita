# Data Pipeline Fix Report

**Date**: 2026-09-04 07:11

**Source**: `(asli)req_data_rut (baru).xlsx`

**Pipeline**: Bronze -> Silver -> Gold -> Feature Store (all `_fix` suffix)

## 1. Bronze Layer

| Table | Rows |
|-------|------|
| data_referensi_mahasiswa_fix | 37655 |
| data_khs_fix | 28273 |
| data_program_studi_fix | 44 |
| data_kelas_fix | 3540 |
| data_kurikulum_fix | 147 |

## 2. Silver Layer

| Table | Rows | Removed |
|-------|------|---------|
| silver_referensi_mahasiswa_fix | 32703 | 4952 |
| silver_khs_fix | 27843 | 430 |

**Cleaning Rules:**
- NULL tanggal_masuk removed
- tanggal_keluar < tanggal_masuk removed
- Duplicate id_mahasiswa removed
- IP = 0 preserved as valid

## 3. Gold Layer

| Table | Rows |
|-------|------|
| dim_mahasiswa_fix | 32703 |
| fact_khs_fix | 27843 |

**Logic (unchanged):**
- LEFT JOIN silver_referensi + silver_khs
- TARGET_SKS: {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}
- IP = 0 included in IPK average
- lama_studi only for LULUS
- AKTIF 2019-2021 = Terlambat

## 4. Feature Store

### Training

- Total: **15599**
- Features: jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks

| Label | Count | % |
|-------|-------|---|
| Tepat Waktu (0) | 3153 | 20.21% |
| Terlambat (1) | 12446 | 79.79% |

**Composition:**
- LULUS 2012-2021: labeled by lama_studi
- AKTIF 2019-2021: label=Terlambat

### Inference

- Total: **12338**

| Angkatan | Count |
|----------|-------|
| 2022 | 4081 |
| 2023 | 3985 |
| 2024 | 4272 |

**Composition:** LULUS 2022 + AKTIF 2022-2024

## 5. Saved Files

### Excel (in Data/)

| File | Rows | Cols | Status |
|------|------|------|--------|
| bronze_referensi_mahasiswa_fix.xlsx | 37655 | 8 | OK |
| bronze_khs_fix.xlsx | 28273 | 4 | OK |
| bronze_program_studi_fix.xlsx | 44 | 3 | OK |
| bronze_kelas_fix.xlsx | 3540 | 3 | OK |
| bronze_kurikulum_fix.xlsx | 147 | 2 | OK |
| silver_referensi_mahasiswa_fix.xlsx | 32703 | 8 | OK |
| silver_khs_fix.xlsx | 27843 | 4 | OK |
| gold_dim_mahasiswa_fix.xlsx | 32703 | 18 | OK |
| gold_fact_khs_fix.xlsx | 27843 | 4 | OK |
| training_dataset_fix.xlsx | 15599 | 10 | OK |
| inference_dataset_fix.xlsx | 12338 | 9 | OK |

### Parquet (in /opt/airflow/parquet_fix/)

- `/opt/airflow/parquet_fix/data_referensi_mahasiswa_fix/`
- `/opt/airflow/parquet_fix/data_khs_fix/`
- `/opt/airflow/parquet_fix/data_program_studi_fix/`
- `/opt/airflow/parquet_fix/data_kelas_fix/`
- `/opt/airflow/parquet_fix/data_kurikulum_fix/`
- `/opt/airflow/parquet_fix/silver_referensi_mahasiswa_fix/`
- `/opt/airflow/parquet_fix/silver_khs_fix/`
- `/opt/airflow/parquet_fix/dim_mahasiswa_fix/`
- `/opt/airflow/parquet_fix/fact_khs_fix/`
- `/opt/airflow/parquet_fix/training_dataset_fix/`
- `/opt/airflow/parquet_fix/inference_dataset_fix/`

### MinIO / Iceberg

| Schema | Table | Parquet Files | Status |
|--------|-------|---------------|--------|
| bronze | data_referensi_mahasiswa_fix | 1 | PASS |
| bronze | data_khs_fix | 1 | PASS |
| bronze | data_program_studi_fix | 1 | PASS |
| bronze | data_kelas_fix | 1 | PASS |
| bronze | data_kurikulum_fix | 1 | PASS |
| silver | silver_referensi_mahasiswa_fix | 2 | PASS |
| silver | silver_khs_fix | 2 | PASS |
| gold | dim_mahasiswa_fix | 1 | PASS |
| gold | fact_khs_fix | 2 | PASS |
| feature_store | training_dataset_fix | 1 | PASS |
| feature_store | inference_dataset_fix | 1 | PASS |

## 6. Validation

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Gold dim_mahasiswa = 32703 | 32703 | 32703 | PASS |
| Gold fact_khs = Silver KHS | 27843 | 27843 | PASS |
| Training > 0 | > 0 | 15599 | PASS |
| Inference > 0 | > 0 | 12338 | PASS |
| All tables use _fix suffix | True | True | PASS |
| All Excel exports OK | True | True | PASS |
| All MinIO objects exist | True | True | PASS |
| No old data mixed | True | True | PASS |
| IP=0 preserved | True | True | PASS |

- IP = 0 in training: 0 rows (preserved)
- IP = 0 in inference: 20 rows (preserved)
- All outputs use _fix suffix: YES
- No old data mixed: YES

## Overall: ALL PASS
