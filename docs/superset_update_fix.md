# Superset Update - Fix

**Date**: 2026-09-04  
**Dashboard**: Dashboard Akademik Mahasiswa  
**Dashboard ID**: 4  
**URL**: http://localhost:8088/superset/dashboard/4/

---

## 1. Source Data

| Source | Table | Count | Status |
|--------|-------|-------|--------|
| Gold | `iceberg.gold.dim_mahasiswa` | 32,703 | ✅ Verified |
| Gold | `iceberg.gold.fact_khs` | 27,843 | ✅ Verified |

---

## 2. Dataset Superset

| Dataset ID | Table Name | Schema | Database | Columns |
|-----------|------------|--------|----------|---------|
| 27 | dim_mahasiswa | gold | Academic Trino | 18 |

---

## 3. Superset Repair

### Problem

Dashboard sebelumnya memiliki chart reference yang tidak lagi memiliki chart definition atau query context.

### Root Cause

1. Chart lama menggunakan dataset ID=5 (`data_referensi_mahasiswa`) yang tidak memiliki kolom `ip`, `sks`, `sks_seharusnya`, `label`
2. Chart baru dibuat tanpa `query_context` - ini menyebabkan error "Chart has no query context saved"
3. Tanpa `query_context`, chart tidak dapat dirender di dashboard

### Action

1. Semua chart lama dihapus (18 chart)
2. 18 chart baru dibuat menggunakan dataset ID=27 (`dim_mahasiswa`)
3. `query_context` digenerate untuk setiap chart
4. Dashboard layout dibangun ulang

### Validation

Semua 18 chart divalidasi:
- Chart ID valid
- Dataset benar (dim_mahasiswa)
- Kolom tersedia
- `query_context` tersedia
- Data dapat di-query (tested via API)

---

## 4. Total Data

| Metrik | Gold | Superset | Selisih |
|--------|------|----------|---------|
| Total rows | 32,703 | 32,703 | 0 |
| Unique ID | 32,703 | 32,703 | 0 |

---

## 5. Dashboard

| Property | Value |
|----------|-------|
| ID | 4 |
| Title | Dashboard Akademik Mahasiswa |
| Published | True |
| Charts | 18 |
| Filters | Angkatan, Jenis Kelamin, Status Mahasiswa, Status Kelulusan |

---

## 6. KPI

| KPI | Chart ID | Formula | Status |
|-----|----------|---------|--------|
| Total Mahasiswa | 127 | COUNT(DISTINCT id_mahasiswa) | ✅ |
| Mahasiswa Aktif | 128 | COUNT(DISTINCT CASE WHEN status='AKTIF') | ✅ |
| Mahasiswa Lulus | 129 | COUNT(DISTINCT CASE WHEN status='Lulus') | ✅ |
| Tepat Waktu | 130 | COUNT(DISTINCT CASE WHEN label=0) | ✅ |
| Terlambat | 131 | COUNT(DISTINCT CASE WHEN label=1) | ✅ |
| Rata-rata IPK | 132 | ROUND(AVG(ipk), 2) | ✅ |
| Rata-rata IP | 133 | ROUND(AVG(ip), 2) | ✅ |
| Rata-rata Total SKS | 134 | ROUND(AVG(total_sks), 1) | ✅ |

---

## 7. Distribusi Angkatan

| Angkatan | Jumlah | Persentase |
|----------|--------|-----------|
| 2012 | 49 | 0.15% |
| 2013 | 33 | 0.10% |
| 2014 | 66 | 0.20% |
| 2015 | 397 | 1.21% |
| 2016 | 1,295 | 3.96% |
| 2017 | 1,579 | 4.83% |
| 2018 | 2,535 | 7.75% |
| 2019 | 3,663 | 11.20% |
| 2020 | 4,566 | 13.96% |
| 2021 | 4,697 | 14.36% |
| 2022 | 4,873 | 14.90% |
| 2023 | 4,447 | 13.60% |
| 2024 | 4,503 | 13.77% |
| **TOTAL** | **32,703** | **100%** |

---

## 8. Status Mahasiswa

| Status | Jumlah | Persentase |
|--------|--------|-----------|
| AKTIF | 14,945 | 45.70% |
| Lulus | 13,328 | 40.76% |
| Mengundurkan diri | 2,567 | 7.85% |
| Dikeluarkan | 1,795 | 5.49% |
| Lainnya | 41 | 0.13% |
| Wafat | 27 | 0.08% |

---

## 9. Status Kelulusan

| Status | Jumlah | Persentase |
|--------|--------|-----------|
| Tepat Waktu | 3,192 | 20.59% |
| Terlambat | 12,580 | 81.08% |
| NULL | 16,931 | - |

---

## 10. Data Quality

| Check | Status |
|-------|--------|
| No duplicate ID | ✅ PASS |
| Gold grain = 1 mahasiswa | ✅ PASS |
| IP = 0 preserved | ✅ PASS |
| Angkatan 2022 visible | ✅ PASS |
| Angkatan 2023 visible | ✅ PASS |
| Angkatan 2024 visible | ✅ PASS |

---

## 11. Machine Learning

Machine Learning belum dimasukkan ke Superset karena model dan inference masih dalam tahap perbaikan.

---

## 12. Charts Summary

| # | Chart Name | Type | Chart ID | Rows | Status |
|---|------------|------|----------|------|--------|
| 1 | Total Mahasiswa | big_number_total | 127 | 1 | ✅ |
| 2 | Mahasiswa Aktif | big_number_total | 128 | 1 | ✅ |
| 3 | Mahasiswa Lulus | big_number_total | 129 | 1 | ✅ |
| 4 | Tepat Waktu | big_number_total | 130 | 1 | ✅ |
| 5 | Terlambat | big_number_total | 131 | 1 | ✅ |
| 6 | Rata-rata IPK | big_number_total | 132 | 1 | ✅ |
| 7 | Rata-rata IP | big_number_total | 133 | 1 | ✅ |
| 8 | Rata-rata Total SKS | big_number_total | 134 | 1 | ✅ |
| 9 | Distribusi Mahasiswa per Angkatan | echarts_timeseries_bar | 135 | 13 | ✅ |
| 10 | Distribusi Status Mahasiswa | pie | 136 | 6 | ✅ |
| 11 | Distribusi Status Kelulusan | pie | 137 | 3 | ✅ |
| 12 | Status Kelulusan per Angkatan | echarts_timeseries_bar | 138 | 30 | ✅ |
| 13 | Status Mahasiswa per Angkatan | echarts_timeseries_bar | 139 | 49 | ✅ |
| 14 | Distribusi Jenis Kelamin | pie | 140 | 2 | ✅ |
| 15 | Rata-rata IPK per Angkatan | echarts_bar | 141 | 13 | ✅ |
| 16 | Rata-rata IP per Angkatan | echarts_bar | 142 | 13 | ✅ |
| 17 | Rata-rata Total SKS per Angkatan | echarts_bar | 143 | 13 | ✅ |
| 18 | Rata-rata Selisih SKS per Angkatan | echarts_bar | 144 | 13 | ✅ |
