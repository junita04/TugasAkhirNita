# Feature Store Training Report (fix)

**Date**: 2026-09-04 06:56

## Summary

- Total training: 15599
- Features: ['jk_enc', 'angkatan', 'ip', 'ipk', 'total_sks', 'jumlah_mk', 'sks_seharusnya', 'selisih_sks']

## Label Distribution

| Label | Count |
|-------|-------|
| Terlambat (1) | 12446 |
| Tepat Waktu (0) | 3153 |

## Angkatan Distribution

| Angkatan | Count |
|----------|-------|
| 2012 | 46 |
| 2013 | 32 |
| 2014 | 41 |
| 2015 | 279 |
| 2016 | 968 |
| 2017 | 1250 |
| 2018 | 2075 |
| 2019 | 3042 |
| 2020 | 3732 |
| 2021 | 4040 |
| 2022 | 94 |

## Status Distribution

| Status | Count |
|--------|-------|
| AKTIF | 2418 |
| Lulus | 13181 |

## Validation

- AKTIF 2022-2024 in training: 0 (must be 0)
- NULL features after dropna: 0
- Duplicate IDs: 0

## Composition

- LULUS angkatan 2012-2021: labeled by lama_studi
- AKTIF angkatan 2019-2021: label = Terlambat
