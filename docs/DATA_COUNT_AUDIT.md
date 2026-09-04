# Data Count Audit

**Tanggal:** 2026-09-02  
**Status:** ✅ AUDIT SELESAI

---

## 1. DATA COUNT SUMMARY

### Bronze Layer
| Table | Row Count |
|-------|-----------|
| data_referensi_mahasiswa | 37,655 |
| data_khs | 29,273 |
| data_kelas | 3,540 |
| data_kurikulum | 147 (999 raw) |
| data_program_studi | 44 (999 raw) |

### Silver Layer
| Table | Row Count | Removed | Alasan |
|-------|-----------|---------|--------|
| silver_mahasiswa | 32,703 | 4,952 | 4,943 null tanggal_masuk + 9 invalid dates |
| silver_khs | 27,843 | 1,430 | null ip/sks, invalid values |
| silver_kelas | 3,540 | 0 | - |
| silver_kurikulum | 147 | 0 | - |
| silver_program_studi | 44 | 0 | - |

### Gold Layer
| Table | Row Count | Source |
|-------|-----------|--------|
| dim_mahasiswa | 32,703 | silver_mahasiswa (LEFT JOIN fact_khs) |
| fact_khs | 27,843 | silver_khs |

---

## 2. BRONZE → SILVER RECONCILIATION

### Mahasiswa
```
Bronze:      37,655
  - Null Tanggal Masuk: 4,943
  - Tgl Keluar < Tgl Masuk: 9 (data tidak valid)
Silver:      32,703
```

### KHS
```
Bronze:      29,273
  - Null IP: ~1,000+
  - Null SKS: ~100+
  - Invalid values: ~300+
Silver:      27,843
```

---

## 3. SILVER → GOLD RECONCILIATION

```
Silver mahasiswa: 32,703
Gold dim_mahasiswa: 32,703
Selisih: 0 (tidak ada row multiplication)
```

---

## 4. GOLD → FEATURE STORE

### Training Dataset
```
Gold (labeled): 15,772
  - IP NULL: 173
Training final: 15,599
```

### Inference Dataset
```
Gold (AKTIF 2022-2024): 12,501
  - IP NULL: 257
Inference final: 12,244
```

---

## 5. DATA YANG DIHAPUS DARI SILVER

### 4,943 Mahasiswa dengan Tanggal Masuk NULL
- Alasan: Tanggal Masuk kosong/tidak valid
- Tidak dapat digunakan untuk perhitungan semester/angkatan
- Tidak ada imputasi tanggal masuk

### 9 Mahasiswa dengan Tanggal Keluar < Tanggal Masuk
- Alasan: Data tidak valid (tanggal keluar sebelum tanggal masuk)
- Semua status: "Mengundurkan diri"
- Contoh: MHS029168 (masuk 2024-08-15, keluar 2024-06-11)

---

## 6. FINAL COUNTS

| Layer | Count |
|-------|-------|
| Bronze mahasiswa | 37,655 |
| Silver mahasiswa | 32,703 |
| Gold dim_mahasiswa | 32,703 |
| Training dataset | 15,599 |
| Inference dataset | 12,244 |
| Prediction (without SMOTE) | 12,244 |
| Prediction (with SMOTE) | 12,244 |

---

*Audit generated: 2026-09-02*
