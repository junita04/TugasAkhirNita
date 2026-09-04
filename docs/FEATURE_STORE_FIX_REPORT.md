# Feature Store Fix Report

**Date**: 2026-09-04 07:41

## 1. Source

- dim_mahasiswa_fix
- fact_khs_fix

## 2. Training Rule

- LULUS angkatan 2012-2021
- AKTIF angkatan 2019-2021 ??? label Terlambat (1)
- NO angkatan 2022 in training

## 3. Inference Rule

- ALL angkatan 2022-2024 (regardless of status)
- 2022 LULUS ??? inference (NOT training)

## 4. Features

- ['jk_enc', 'angkatan', 'ip', 'ipk', 'total_sks', 'jumlah_mk', 'sks_seharusnya', 'selisih_sks']

## 5. SKS Logic

- sks_seharusnya from Gold (TARGET_SKS mapping)
- selisih_sks = total_sks - sks_seharusnya
- TARGET_SKS: {1: 17, 2: 36, 3: 55, 4: 75, 5: 95, 6: 115, 7: 135, 8: 144}

## 6. Training Distribution

- Total: **15505**
- Tepat Waktu (0): 3059 (19.73%)
- Terlambat (1): 12446 (80.27%)

| Angkatan | Status | Label | Jumlah |
|----------|--------|-------|--------|
| 2012 | LULUS | Terlambat | 46 |
| 2013 | LULUS | Terlambat | 32 |
| 2014 | LULUS | Terlambat | 41 |
| 2015 | LULUS | Terlambat | 279 |
| 2016 | LULUS | Tepat Waktu | 52 |
| 2016 | LULUS | Terlambat | 916 |
| 2017 | LULUS | Tepat Waktu | 166 |
| 2017 | LULUS | Terlambat | 1084 |
| 2018 | LULUS | Tepat Waktu | 280 |
| 2018 | LULUS | Terlambat | 1795 |
| 2019 | LULUS | Tepat Waktu | 1149 |
| 2019 | LULUS | Terlambat | 1576 |
| 2019 | AKTIF | Terlambat | 317 |
| 2020 | LULUS | Tepat Waktu | 613 |
| 2020 | LULUS | Terlambat | 2336 |
| 2020 | AKTIF | Terlambat | 783 |
| 2021 | LULUS | Tepat Waktu | 799 |
| 2021 | LULUS | Terlambat | 1923 |
| 2021 | AKTIF | Terlambat | 1318 |

## 7. Inference Distribution

- Total: **12338**
- Angkatan 2022: 4081
- Angkatan 2023: 3985
- Angkatan 2024: 4272

## 8. Critical Validation

| Check | Result | Status |
|-------|--------|--------|
| 2022 in training | 0 | PASS |
| 2022 in inference | 4081 | PASS |
| Overlap training-inference | 0 | PASS |
| Duplicate in training | 0 | PASS |
| Duplicate in inference | 0 | PASS |
| Missing key | train=0, inf=0 | PASS |
| 8 features (training) | PASS | PASS |
| 8 features (inference) | PASS | PASS |
| SKS logic | PASS | PASS |

- Total unique mahasiswa (training + inference): 27843
- Gold dim_mahasiswa_fix: 32703
- Gold unique: 32703

## 9. Output

- training_dataset_fix: 15505 rows
- inference_dataset_fix: 12338 rows

## 10. Status

PASS
