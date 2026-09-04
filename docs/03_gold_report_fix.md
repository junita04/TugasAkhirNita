# Gold Layer Report (fix)

**Date**: 2026-09-04 06:55

## JOIN Validation

- Silver mahasiswa: 32703
- Silver KHS: 27843
- Unique KHS mahasiswa: 27843
- Gold (after LEFT JOIN): 32703
- Unique ID Gold: 32703
- Mahasiswa with KHS: 27843

## Status Distribution

| Status | Count |
|--------|-------|
| AKTIF | 14945 |
| Dikeluarkan | 1795 |
| Lainnya | 41 |
| Lulus | 13328 |
| Wafat | 27 |
| Mengundurkan diri | 2567 |

## Label Distribution (Training)

| Label | Count |
|-------|-------|
| Terlambat | 12580 |
| Tepat Waktu | 3192 |

## TARGET_SKS Mapping

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

## Notes

- IP = 0 included in average calculation
- LEFT JOIN preserves all mahasiswa
- lama_studi only for LULUS
- AKTIF 2019-2021 labeled as Terlambat
