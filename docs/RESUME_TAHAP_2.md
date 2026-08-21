# Resume Tahap 2 — Pipeline Bronze → Silver → Gold → JOIN dengan Dataset Baru

> Dokumen ini adalah laporan eksekusi (Stage 2) pipeline dengan dataset baru
> `(asli)req_data_rut (1).xlsx` untuk revisi final skripsi
> "Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model
> Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis
> Machine Learning".
>
> **Aturan tahap ini:** proses dataset baru melalui Bronze → Silver → Gold →
> JOIN fakta-dimensi → validasi Gold; TIDAK menyentuh Feature Store, ML, SMOTE,
> inference, Airflow, maupun Superset. Output lama diamankan (backup `_lama`),
> tidak ada output lama yang dihapus. Waktu eksekusi diukur nyata.

## 1. Perubahan Kode

| File | Perubahan | Alasan |
|---|---|---|
| `backend/silver/silver.py` | Tambah pemetaan kolom `ID_MHS` → `id_mahasiswa` pada `SILVER_SPECS` untuk `data_referensi_mahasiswa` dan `data_khs` | Nama kolom id berubah di dataset baru (`ID` → `ID_MHS`); pemetaan lama `ID` tetap dipertahankan agar kompatibel dengan dataset lama |
| `backend/services/pipeline_entry.py` | `DEFAULT_FILENAME` diubah dari `req_data_rut.xlsx` (tidak ada di `data/`) menjadi `(asli)req_data_rut (1).xlsx` | File default lama tidak pernah ada sehingga resolusi file gagal |
| `scripts/test_pipeline_trigger.py` | Harapan default diperbarui ke nama file baru | Menjaga konsistensi test dengan `DEFAULT_FILENAME` |

Tidak ada pipeline baru yang dibuat. Bronze, Silver, dan Gold memakai modul
lama yang dimodifikasi seperlunya (lihat `backend/bronze/bronze.py`,
`backend/silver/silver.py`, `backend/gold/*`).

Catatan environment: Spark lokal di host Windows memerlukan `winutils.exe` +
`hadoop.dll`. Karena tidak tersedia di sistem, keduanya diunduh (winutils 3.5.0
build dari `notepass/hadoop-native-win-libs`) ke `%TEMP%\opencode\hadoop\bin` dan
`HADOOP_HOME` diset saat menjalankan pipeline. Ini perubahan environment, bukan
perubahan kode/struktur data.

## 2. Dataset yang Diproses

- File: `data\(asli)req_data_rut (1).xlsx`
- Sheet (6): Referensi Data Mahasiswa, Data Program Studi, Data Mata Kuliah,
  Data Kelas, Data Kurikulum, Data KHS.
- `Data Mata Kuliah` kosong → di-skip Bronze (tidak dibuatkan data palsu).

## 3. Hasil Bronze

Bronze menyimpan data mentah sebagaimana sumber (nama tabel dibakukan, nilai
tidak diubah).

| Tabel Bronze | Rows | Kolom |
|---|---|---:|---|
| `bronze.data_referensi_mahasiswa` | 37.655 | 8 (`ID_MHS`, Jenis Kelamin, Tanggal Masuk, Tanggal Keluar, IPK, Total SKS, Jumlah MK, Status Mahasiswa) |
| `bronze.data_khs` | 28.273 bernilai + 1.000 baris kosong | 4 (`ID_KHS`, `ID_MHS`, IP, SKS) |
| `bronze.data_program_studi` | 44 bernilai + 955 baris kosong | 3 (Kode, Nama Program Studi, Jumlah Dosen) |
| `bronze.data_kelas` | 3.540 | 3 (nama_kelas, nama_mk, kuota) |
| `bronze.data_kurikulum` | 147 bernilai + 852 baris kosong | 2 (Nama Kurikulum, Jumlah SKS Total) |
| `bronze.data_mata_kuliah` | — | Sheet kosong, tidak dibuat |

**Penjelasan selisih baris:** pembaca Excel (spark-excel) membaca seluruh area
lembar kerja termasuk baris kosong ekstra di bawah tabel; Silver membersihkan
baris kosong tersebut. Jumlah baris **berisi nilai** sudah diverifikasi cocok
dengan sumber (KHS 28.273, Program Studi 44, Kurikulum 147). Perilaku ini
konsisten dengan pipeline lama.

## 4. Hasil Silver

Silver menormalkan kolom (memetakan `ID_MHS` → `id_mahasiswa`), membersihkan,
memvalidasi, lalu menyimpan.

| Tabel Silver | Awal | Valid | Detail Invalid |
|---|---:|---:|---|
| `silver.silver_mahasiswa` | 37.655 | 32.703 | duplicate_id 0, null_id 0, null_tanggal_masuk 4.943, keluar_sebelum_masuk 9, ipk_out_of_range 0, ipk_null 0, sks_negatif 0, jumlah_mk_negatif 0, status_unknown 0 |
| `silver.silver_khs` | 28.273 | 28.273 | duplicate_id 0, null_id 0, null_ip 0, null_sks 0, ip_negatif 0, ip_atas_4 0, sks_negatif 0; ip_sama_dengan_nol 92 (dipertahankan), sks_sama_dengan_nol 0 |
| `silver.silver_program_studi` | 44 | 44 | — |
| `silver.silver_kelas` | 3.540 | 3.540 | — |
| `silver.silver_kurikulum` | 147 | 147 | — |

Verifikasi `id_mahasiswa` terbentuk dengan benar dari `ID_MHS`:
- `silver_mahasiswa` null id = 0; contoh: `MHS1`/`AKTIF`/IPK 2.26.
- `silver_khs` null id = 0; contoh: `MHS1`/IP 2.64/SKS 145.

Hasil join referensi ↔ KHS di level Silver:
- `silver_mahasiswa` unique id : 32.703
- `silver_khs` unique id : 28.273
- KHS id tidak ada di referensi : 0
- Referensi tanpa KHS : 4.430
- Referensi ada KHS : 28.273

Angka di atas konsisten dengan audit Tahap 1. Data Quality Report tersimpan di
`logs/data_quality_report.json`.

## 5. Hasil Gold

Gold membentuk star schema (dimension + fact) dengan sumber HANYA dari Silver.

| Tabel Gold | Rows | Keterangan |
|---|---:|---|
| `gold.dim_mahasiswa` | 32.703 | 8 kolom, PK `id_mahasiswa` |
| `gold.fact_khs` | 28.273 | 3 kolom (`id_mahasiswa`, `ip`, `sks`), FK `id_mahasiswa` |
| `gold.gold_program_studi` | 44 | — |
| `gold.gold_kurikulum` | 147 | — |

Hasil validasi star schema (`process_gold` → `_validate_star_schema`):
- Dim: rows 32.703 = distinct 32.703 (dup 0), null PK 0 → GRAIN PASS.
- Fact: rows 28.273 = distinct 28.273 (dup 0), null id/IP/SKS 0 → GRAIN PASS.
- Referential integrity: fact tanpa dim (orphan) = 0 → PASS; dim tanpa fact =
  4.430.
- Join validation (dim LEFT JOIN fact): join rows 32.703 = dim rows
  (row multiplication 0) → PASS; matching (ada fact) 28.273; non-matching 4.430.

## 6. Hasil JOIN Fakta-Dimensi

Tabel JOIN `gold.gold_mahasiswa_fakta` (dim_mahasiswa LEFT JOIN fact_khs,
10 kolom) dibuat dan disimpan ke Iceberg.

| Metrik | Nilai | Status |
|---|---:|---|
| Rows hasil JOIN | 32.703 | — |
| Rows dim (basis) | 32.703 | — |
| Duplicate id pada JOIN | 0 | PASS |
| Null id pada JOIN | 0 | PASS |
| Unmatched (tanpa fact) | 4.430 | sesuai dim_without_fact |
| Row multiplication | 0 | PASS |

Hasil terbaca kembali dari Iceberg (read-back) dengan skema 10 kolom:
`id_mahasiswa`, `jenis_kelamin`, `tanggal_masuk`, `tanggal_keluar`, `ipk`,
`total_sks`, `jumlah_mk`, `status_mahasiswa`, `ip`, `sks`.

## 7. Perubahan Jumlah Data vs Baseline

Dibandingkan tabel lama (sebelum Tahap 2, backup `_lama`), jumlah baris Silver
dan Gold identik — karena himpunan `ID_MHS` dan nilai-nilai referensi/KHS identik
hanya pada nama kolom. Perbedaan nilai IP KHS pada 6.176 baris (dari audit Tahap 1)
ikut terbawa ke `silver_khs`/`fact_khs` (terverifikasi: `ip_diff_rows = 6176`
terhadap `silver_khs_lama`).

## 8. Pengukuran Waktu (nyata, diukur saat eksekusi)

| Tahap | Waktu (detik) |
|---|---:|
| Bronze | 37,84 |
| Silver | 6,23 |
| Gold (termasuk validasi star schema) | 2,04 |
| JOIN fakta-dimensi (build) | 0,33 |
| Validasi JOIN (read-back) | 0,28 |

Total waktu pipeline Bronze→Silver→Gold→JOIN: ± 46,7 detik (tidak termasuk
cold-start Spark / resolusi dependency). Detail tersimpan di
`logs/stage2_results.json`.

## 9. Output yang Disimpan (Iceberg)

Tabel yang dibuat/diperbarui pada Tahap 2 (snapshot baru ber-commit 2026-08-20):

- `bronze.data_referensi_mahasiswa`, `bronze.data_khs`,
  `bronze.data_program_studi`, `bronze.data_kelas`, `bronze.data_kurikulum`
- `silver.silver_mahasiswa`, `silver.silver_khs`,
  `silver.silver_program_studi`, `silver.silver_kelas`, `silver.silver_kurikulum`
- `gold.dim_mahasiswa`, `gold.fact_khs`, `gold.gold_program_studi`,
  `gold.gold_kurikulum`, `gold.gold_mahasiswa_fakta` (JOIN, baru)

## 10. Output Lama (TIDAK dihapus)

Sebelum pipeline dijalankan, 14 tabel yang akan ditimpa di-copy ke versi `_lama`:

- `bronze.*_lama` (5), `silver.*_lama` (5), `gold.dim_mahasiswa_lama`,
  `gold.fact_khs_lama`, `gold.gold_program_studi_lama`,
  `gold.gold_kurikulum_lama`.
- `gold.gold_mahasiswa` (legacy, dibaca Superset) TIDAK ditimpa dan tetap utuh.
- Feature Store / hasil prediksi / hasil pengukuran (`results/*`) tidak disentuh.

Selain itu Iceberg mempertahankan riwayat snapshot; snapshot lama tetap dapat
diakses melalui time-travel bila diperlukan.

## 11. Validasi Akhir

- Pipeline Bronze → Silver → Gold → JOIN berjalan tanpa error kritis: **YA**
- Bronze terbaca & tersimpan: **PASS**
- Silver valid (grain, duplikat, null, referential): **PASS**
- Gold star schema valid: **PASS**
- JOIN fakta-dimensi valid (tanpa row multiplication): **PASS**
- Read-back dari Iceberg berhasil: **YA**
- Output lama aman (backup `_lama` + snapshot history): **YA**
- Dataset baru siap untuk Feature Store (Tahap 3): **YA**

## 12. Kesimpulan

Tahap 2 **selesai**. Dataset baru `(asli)req_data_rut (1).xlsx` berhasil diproses
melalui Bronze → Silver → Gold → JOIN fakta-dimensi dengan perubahan kode minimal
(pemetaan `ID_MHS` dan default filename), semua validasi PASS, waktu eksekusi
terukur, dan seluruh output tersimpan di Iceberg tanpa menghapus output lama.
Aman untuk melanjutkan ke Tahap 3 (Feature Store / training / SMOTE / inference).
