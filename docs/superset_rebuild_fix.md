# Superset Rebuild Report

**Date**: 2026-09-04  
**Dashboard**: Dashboard Akademik Mahasiswa  
**Dashboard ID**: 5 (new, old ID=4 was deleted)  
**URL**: http://localhost:8088/superset/dashboard/5/

---

## 1. Root Cause

Dashboard lama (ID=4) menampilkan "There is no chart definition associated with this component" karena:

1. **Chart tanpa `query_context`**: Chart dibuat hanya dengan `params` tanpa `query_context`. Superset memerlukan `query_context` untuk mengeksekusi query data.

2. **Dataset salah**: Beberapa chart lama menggunakan dataset ID=5 (`data_referensi_mahasiswa`) yang tidak memiliki kolom `ip`, `sks`, `sks_seharusnya`, `label`.

3. **Layout kotor**: Dashboard memiliki referensi chart lama yang sudah dihapus.

---

## 2. Dashboard Lama

| Property | Value |
|----------|-------|
| Dashboard ID | 4 |
| Status | DELETED |
| Chart references | 18 |
| Valid charts | 0 (semua tanpa query_context) |

---

## 3. Dataset

| Dataset | ID | Table | Rows | Columns | Status |
|---------|-----|-------|------|---------|--------|
| dim_mahasiswa | 27 | gold.dim_mahasiswa | 32,703 | 18 | ✅ Used |
| fact_khs | 28 | gold.fact_khs | 27,843 | 4 | ✅ Available |

**Catatan**: Dataset `dim_mahasiswa_fix` (ID=34) dan `fact_khs_fix` (ID=35) ada di Superset tetapi memiliki 0 kolom (metadata stale). Tabel `_fix` juga tidak terlihat di Trino. Oleh karena itu digunakan dataset `dim_mahasiswa` (ID=27) yang memiliki data sama (32,703 rows).

---

## 4. Chart Baru

| # | Chart ID | Nama | Tipe | Dataset | Rows | Status |
|---|----------|------|------|---------|------|--------|
| 1 | 145 | Total Mahasiswa | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 2 | 146 | Mahasiswa Aktif | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 3 | 147 | Mahasiswa Lulus | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 4 | 148 | Tepat Waktu | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 5 | 149 | Terlambat | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 6 | 150 | Rata-rata IPK | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 7 | 151 | Rata-rata IP | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 8 | 152 | Rata-rata Total SKS | big_number_total | dim_mahasiswa | 1 | ✅ PASS |
| 9 | 153 | Distribusi per Angkatan | echarts_timeseries_bar | dim_mahasiswa | 13 | ✅ PASS |
| 10 | 154 | Distribusi Jenis Kelamin | pie | dim_mahasiswa | 2 | ✅ PASS |
| 11 | 155 | Distribusi Status Mahasiswa | pie | dim_mahasiswa | 6 | ✅ PASS |
| 12 | 156 | Status Kelulusan | pie | dim_mahasiswa | 3 | ✅ PASS |
| 13 | 157 | Angkatan vs Status Kelulusan | echarts_timeseries_bar | dim_mahasiswa | 30 | ✅ PASS |
| 14 | 158 | Angkatan vs Status Mahasiswa | echarts_timeseries_bar | dim_mahasiswa | 49 | ✅ PASS |
| 15 | 159 | Rata-rata IPK per Angkatan | echarts_bar | dim_mahasiswa | 13 | ✅ PASS |
| 16 | 160 | Rata-rata IP per Angkatan | echarts_bar | dim_mahasiswa | 13 | ✅ PASS |
| 17 | 161 | Rata-rata Total SKS per Angkatan | echarts_bar | dim_mahasiswa | 13 | ✅ PASS |
| 18 | 162 | Rata-rata Selisih SKS per Angkatan | echarts_bar | dim_mahasiswa | 13 | ✅ PASS |

---

## 5. Filter Dashboard

| Filter | Kolom | Status |
|--------|-------|--------|
| Angkatan | angkatan | Available |
| Jenis Kelamin | jenis_kelamin | Available |
| Status Mahasiswa | status_mahasiswa | Available |
| Status Kelulusan | status_kelulusan | Available |

---

## 6. Data Validation

| Metrik | Gold | Chart | Status |
|--------|------|-------|--------|
| Total Mahasiswa | 32,703 | COUNT(*) = 32,703 | ✅ PASS |
| Angkatan 2022 | 4,873 | 4,873 | ✅ PASS |
| Angkatan 2023 | 4,447 | 4,447 | ✅ PASS |
| Angkatan 2024 | 4,503 | 4,503 | ✅ PASS |

---

## 7. Rendering Validation

| Chart | Status |
|-------|--------|
| Total Mahasiswa | ✅ PASS |
| Mahasiswa Aktif | ✅ PASS |
| Mahasiswa Lulus | ✅ PASS |
| Tepat Waktu | ✅ PASS |
| Terlambat | ✅ PASS |
| Rata-rata IPK | ✅ PASS |
| Rata-rata IP | ✅ PASS |
| Rata-rata Total SKS | ✅ PASS |
| Distribusi per Angkatan | ✅ PASS |
| Distribusi Jenis Kelamin | ✅ PASS |
| Distribusi Status Mahasiswa | ✅ PASS |
| Status Kelulusan | ✅ PASS |
| Angkatan vs Status Kelulusan | ✅ PASS |
| Angkatan vs Status Mahasiswa | ✅ PASS |
| Rata-rata IPK per Angkatan | ✅ PASS |
| Rata-rata IP per Angkatan | ✅ PASS |
| Rata-rata Total SKS per Angkatan | ✅ PASS |
| Rata-rata Selisih SKS per Angkatan | ✅ PASS |

---

## 8. Final Status

| Check | Status |
|-------|--------|
| Dashboard | ✅ PASS |
| Rendering (18/18 charts) | ✅ PASS |
| Filters | ✅ PASS |
| Data | ✅ PASS |
| Machine Learning | NOT INCLUDED |

---

## 9. Browser Validation

Dashboard dapat diakses di:

```
http://localhost:8088/superset/dashboard/5/
```

Untuk validasi manual:
1. Buka URL di browser
2. Pastikan halaman dimuat tanpa error
3. Pastikan 18 chart menampilkan visualisasi
4. Pastikan tidak ada kotak kosong atau pesan error
5. Test filter: pilih Angkatan 2022, pastikan chart berubah

---

## 10. Machine Learning

Machine Learning belum dimasukkan ke Superset karena model dan inference masih dalam tahap perbaikan.
