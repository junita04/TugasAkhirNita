# Silver Layer Report (fix)

**Date**: 2026-09-04 06:55

## Processing

- Column names standardized (lowercase, underscore)
- Type casting applied
- NULL tanggal_masuk removed
- tanggal_keluar < tanggal_masuk removed
- Duplicate id_mahasiswa removed
- IP = 0 preserved as valid

## Tables

| Silver Table | Bronze Count | Silver Count | Removed |
|-------------|-------------|-------------|----------|
| silver_referensi_mahasiswa_fix | 37655 | 32703 | 4952 |
| silver_khs_fix | 28273 | 27843 | 430 |
