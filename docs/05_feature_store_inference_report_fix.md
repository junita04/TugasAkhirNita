# Feature Store Inference Report (fix)

**Date**: 2026-09-04 06:56

## Summary

- Total inference: 12338
- Features: ['jk_enc', 'angkatan', 'ip', 'ipk', 'total_sks', 'jumlah_mk', 'sks_seharusnya', 'selisih_sks']

## Angkatan Distribution

| Angkatan | Count |
|----------|-------|
| 2022 | 4081 |
| 2023 | 3985 |
| 2024 | 4272 |

## Status Distribution

| Status | Count |
|--------|-------|
| AKTIF | 12244 |
| Lulus | 94 |

## Validation

- Training data in inference: 94 (must be 0)
- NULL features after dropna: 0
- Duplicate IDs: 0

## Snapshot (Januari 2026)

| Angkatan | Semester | Target SKS |
|----------|----------|------------|
| 2022 | 7 | 135 |
| 2023 | 5 | 95 |
| 2024 | 3 | 55 |
