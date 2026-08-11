# Phase 4 — Silver Layer Audit

Audit statis (tanpa menjalankan aplikasi/service) pada **Silver Layer** project Tugas Akhir:

> **"Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis Machine Learning"**

Project utama: `D:\TugasAkhirNita\`

Acuan arsitektur: **Docker-based** (Spark di dalam Docker; Bronze → Silver → Iceberg → MinIO). Hasil transfer dari Phase 2 (Spark+Iceberg+Docker) dan Phase 3 (Bronze) dipakai sebagai konteks, tidak diulang di sini.

---

## 1. Scope

Audit dibatasi pada:

- `backend/silver/silver.py` (inti Silver)
- File yang dipanggil/digunakan Silver: `backend/spark/session.py`, `backend/config/settings.py`, `backend/utils/logger.py`
- Pemanggil Silver: `backend/services/pipeline_service.py`, `backend/services/pipeline_runner.py`, `backend/services/pipeline_state.py`, `scripts/test_silver.py`
- Konfigurasi Iceberg/MinIO (acuan Phase 2) dan output Bronze (acuan Phase 3)
- Konsumen Silver (Gold/Feature Store) **hanya dibaca** untuk memahami kontrak schema/boundary — tidak diubah

Gold, Feature Store, ML, Airflow, Trino, Superset **tidak** diaudit dan **tidak** diubah. Bronze tidak diubah (tidak ditemukan dependency yang membuat Silver gagal berfungsi).

---

## 2. Silver Architecture

```text
Iceberg.bronze.*  (READ)
        ↓  spark.table(f"{ICEBERG_NAMESPACE}.bronze.<table>")
Cleansing & Standardisasi:
        ↓  1) rename kolom (clean_column_name)
        ↓  2) trim seluruh kolom string
        ↓  3) drop baris seluruh-nilai-kosong (na.drop how="all")
        ↓  4) validasi: data_referensi_mahasiswa → filter tanggal_masuk IS NOT NULL
Icering write (OVERWRITE via createOrReplace)
        ↓
Iceberg.silver.*  (WRITE)
        ↓
MinIO (s3a://warehouse/iceberg/silver/...)
```

Proses dijalankan untuk **setiap tabel** hasil `SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze` (dinamis, bukan daftar hardcoded).

---

## 3. Bronze Input

| Aspek | Nilai | Sumber |
|---|---|---|
| Enumerasi input | `spark.sql("SHOW TABLES IN " + ICEBERG_NAMESPACE + ".bronze")` → `row.tableName` | `silver.py:110`, `:%40` |
| Catalog | `ICEBERG_NAMESPACE` (= `iceberg` pada cluster, `local` pada mode local) | `settings.py:62` |
| Pembacaan | `spark.table(f"{ICEBERG_NAMESPACE}.bronze.{table_name}")` | `silver.py:39` |
| Tabel input yang diharapkan | `bronze.data_referensi_mahasiswa`, `bronze.data_khs`, `bronze.data_program_studi`, `bronze.data_kurikulum` | bronze Phase 3, docs |
| Schema input | kolom asli dari Excel (contoh `Status Mahasiswa`, `Tanggal Masuk`, `IPK`, `Total SKS`, `Jumlah MK`, `Jenis Kelamin`, dst.), tipe dari `inferSchema` Bronze | bronze Phase 3 |

**Konsistensi:** tidak ada literal `local.bronze.*`, `lakehouse.bronze.*`, maupun hardcode nama tabel. Semua referensi memakai `ICEBERG_NAMESPACE` → konsisten dengan keputusan Phase 2. **Verdict: input sesuai.**

---

## 4. Cleaning & Standardization

| Operasi | Kolom | Lokasi | Keterangan |
|---|---|---|---|
| Rename kolom | seluruh kolom | `silver.py:47-52` | `clean_column_name`: `strip().lower()`, spasi/`-`/`/`→`_`, buang `(`/`)`, lalu `re.sub(r"[^a-zA-Z0-9_]", "", ...)`. Contoh: `Status Mahasiswa` → `status_mahasiswa` |
| Trim | seluruh kolom bertipe `string` | `silver.py:58-65` | `trim(col(...))` menghapus spasi tepi nilai |
| Drop baris semua-kosong | seluruh kolom | `silver.py:71` | `df.na.drop(how="all")` — hanya baris yang **seluruh** nilainya null |

Tidak ada normalisasi nilai (case/value transform) pada data — normalisasi diterapkan hanya pada **nama kolom** dan **trim spasi**. Nilai huruf besar/kecil dibiarkan sampai digunakan (Gold, `trim`+`upper` saat label).

---

## 5. Missing Value Handling

| Operasi | Kondisi | Kolom | Potensi Data Loss | Penilaian |
|---|---|---|---|---|
| `df.na.drop(how="all")` | baris dengan seluruh kolom null | semua | Rendah — hanya baris "baris kosong" dari Excel | Aman; baris dengan 1+ nilai ada dipertahankan |
| `filter(col("tanggal_masuk").isNotNull())` | `tanggal_masuk` NULL | hanya `data_referensi_mahasiswa` | **Potensi kehilangan record mahasiswa** bila tanggal masuk tidak terisi di sumber | Cleansing karena field wajib untuk perhitungan lama studi; **NEEDS RUNTIME VERIFICATION** jumlah baris terdampak |

Pemahaman konteks akademik:
- `tanggal_keluar` NULL (mahasiswa aktif/belum lulus) → **tidak** dihapus; Silver menganggap ini kondisi valid dan Gold memakainya untuk lama studi via `current_date()`. Penggunaan `how="all"` dan filter yang hanya `tanggal_masuk` memastikan mahasiswa aktif tetap ada. ✅ konsisten dengan makna "belum lulus/aktif".
- Tidak ada asumsi bahwa NULL=0 / NULL=dihapus selain dua operasi di atas.

**Catatan:** drop `tanggal_masuk` NULL tidak disertai laporan/statistik. Disarankan mencatat jumlah baris yang dibuang (direkomendasikan, bukan kerja wajib audit).

---

## 6. Duplicate Handling

- **Tidak ada** `dropDuplicates`, `drop_duplicates`, `distinct` di `backend/silver/silver.py` (hasil grep).
- Duplicate baris yang ada di Bronze **dipertahankan** menuju Silver.
- Konsekuensi: downstream (Gold/Feature Store) menerima baris duplikat sesuai sumber — konsisten dengan sifat Bronze "tanpa dedup".

**Verdict:** tidak menghapus duplicate otomatis; aman. Tidak ada business key yang dipakai untuk dedup di Silver.

---

## 7. Datatype & Date Handling

| Aspek | Kondisi di Silver | Keterangan |
|---|---|---|
| `cast()` | **tidak digunakan** | Perubahan tipe (IPK→double, total_sks/jumlah_mk→int, tanggal→date) dilakukan di **Gold** (`gold_mahasiswa.py`), sesuai dokumen `REVIEW_PROJECT.md:191` |
| `to_date()` / `to_timestamp()` | tidak digunakan | Parsing tanggal ada di Gold dan `batch_prediction_service` |
| `astype()` | tidak digunakan | — |
| `withColumn()` | hanya untuk `trim` | tidak ada konversi tipe |
| Tanggal masuk/keluar | dibiarkan sebagai tipe inferensi Bronze | Format aktual hanya dapat dipastikan saat runtime → **NEEDS RUNTIME VERIFICATION** |

Risiko: karena tipe di-Silver adalah tipe hasil `inferSchema=true` Bronze, pemotongan presisi/leading-zero pada NIM/kode sudah terjadi di Bronze (temuan Phase 3, masih relevan). Tidak dilakukan konversi di Silver untuk menghindari NULL baru secara tidak sengaja.

---

## 8. Filtering

| Filter | Lokasi | Kondisi | Data yang dibuang |
|---|---|---|---|
| `filter(col("tanggal_masuk").isNotNull())` | `silver.py:85-87` | `tanggal_masuk` NULL, khusus `data_referensi_mahasiswa` | baris mahasiswa tanpa tanggal masuk |

Penilaian: filter ini adalah **cleansing** (menghapus baris yang tidak bisa diproses karena field wajib kosong), bukan business rule KPI, bukan feature engineering. Sesuai kepentingan Silver. Tidak ditambahkan filter lain.

---

## 9. Transformation Boundary

Silver hanya melakukan:
- rename kolom,
- trim spasi,
- drop baris semua-kosong,
- filter `tanggal_masuk` NULL khusus mahasiswa.

**Tidak ada** di Silver:
- aggregation, business KPI, feature engineering, target/label creation (`status_kelulusan`), student classification, join antar-tabel.

Semua logic tersebut berada di Advanced Placeholders Gold (`gold_mahasiswa.py`, `gold_prodi.py`, `gold_kurikulum.py`) dan Feature Store. **Boundary bersih — tidak ada pelanggaran.**

> Catatan kunci di Gold (hanya dibaca, tidak diubah): `gold_mahasiswa.py` melakukan join implisit mengambil `jumlah_sks_total` dari `silver.data_kurikulum` sebagai konstanta — berada di layer Gold, sesuai arsitektur.

---

## 10. Silver Tables

| Input Bronze | Output Silver | Catalog | Namespace | Format |
|---|---|---|---|---|
| `bronze.data_referensi_mahasiswa` | `silver.data_referensi_mahasiswa` | `iceberg` | `silver` | Iceberg |
| `bronze.data_khs` | `silver.data_khs` | `iceberg` | `silver` | Iceberg |
| `bronze.data_program_studi` | `silver.data_program_studi` | `iceberg` | `silver` | Iceberg |
| `bronze.data_kurikulum` | `silver.data_kurikulum` | `iceberg` | `silver` | Iceberg |

*(Enumerasi dinamis `SHOW TABLES IN bronze` → setiap tabel Bronze punya pasangan Silver 1:1 dengan nama sama.)*

Penulisan: `df.writeTo(f"{ICEBERG_NAMESPACE}.silver.{table_name}").using("iceberg").createOrReplace()` — `silver.py:96-98`.

- Catalog: `iceberg` (HMS `thrift://hive-metastore:9083`, warehouse `s3a://warehouse/iceberg`) — konsisten Phase 2.
- Namespace `silver` dibuat otomatis oleh `get_spark` (`CREATE NAMESPACE IF NOT EXISTS`).
- Mode tulis: **`createOrReplace()` = OVERWRITE penuh** setiap run (bukan append/history). Konsisten dengan keputusan Bronze; berimplikasi tanpa riwayat versi.

---

## 11. Data Loss Analysis

| Operasi | Lokasi | Berpotensi menghapus record? | Alasan dari kode |
|---|---|---|---|
| `na.drop(how="all")` | `silver.py:71` | Hampir tidak — hanya baris kosong total | Pembersihan junk row dari Excel; baris berisi 1+ nilai tetap ada |
| `filter(tanggal_masuk IS NOT NULL)` | `silver.py:85-87` | Ya — record mahasiswa tanpa tanggal masuk | Field wajib untuk lama studi; **perlu verifikasi runtime** jumlah baris |
| rename / trim | `silver.py:47-65` | Tidak | hanya mengubah nama/nilai |
| `createOrReplace()` | `silver.py:98` | Menghapus data Silver sebelumnya (overwrite) | Overwrite penuh — data Silver tidak memiliki riwayat; bila file berubah antar-run, data lama tergantikan |
| join / select / drop / distinct | none | — | tidak digunakan |

Tidak ada operasi join, `drop`, `where` lain, maupun `distinct` yang menghilangkan data di Silver.

---

## 12. Findings

### Critical
- Tidak ada.

### High
- Tidak ada yang terbukti murni statis.

### Medium
1. **`get_spark` dipanggil per tabel → SparkSession dibuat berulang.** `process_all_tables` membuat session (untuk `SHOW TABLES`), lalu untuk setiap tabel `process_table` memanggil `get_spark("Silver Layer")` lagi. Karena `get_spark` men-stop session aktif lalu `getOrCreate`, terjadi churn session (restart SparkContext) untuk tiap tabel. Berfungsi secara fungsional tetapi **boros resource** di mode cluster dan bertentangan dengan prinsip single-session. `spark.stop()` di akhir justru men-stop session pertama yang sudah di-stop, sedangkan session terakhir tidak pernah di-stop eksplisit.
2. **`clean_column_name` berpotensi menghasilkan nama kolom duplikat.** Misal dua kolom sumber `A B` dan `A-B` → sama-sama `a_b`; `withColumnRenamed` menghasilkan nama ganda yang bisa membuat operasi `col("a_b")` ambigu. Tergantung data → **NEEDS RUNTIME VERIFICATION**.

### Low
3. Filter `tanggal_masuk` NULL hanya berlaku untuk `data_referensi_mahasiswa`; tidak ada laporan/statistik baris yang dibuang (data quality trace).
4. `df.count()` dijalankan 2× per tabel (`Rows Awal`/`Rows Akhir`) + pemanggilan full-scan — overhead kecil.
5. Tidak ada `try/except` di `process_table`: satu tabel gagal → seluruh tahap Silver gagal (state di-patch `failed` oleh pipeline_runner). Tampil di pipeline monitoring, tetapi tidak ada proses tabel yang berhasil tersimpan/ter-log partial.
6. Tidak ada validasi kesesuaian schema/nama kolom saat membaca Bronze → `col("tanggal_masuk")` pada mahasiswa akan error bila kolom tak tersedia (seharusnya tersedia dari data aktual).

### Needs Runtime Verification
1. Jumlah baris Bronze vs Silver per tabel (berapa line yang hilang oleh `na.drop how="all"` dan filter `tanggal_masuk`).
2. Tipe/format tanggal aktual di tabel Bronze (`inferSchema` menghasilkan string vs date) — menentukan keberhasilan cast di Gold.
3. Apakah terjadi kolom duplikat hasil `clean_column_name` pada dataset aktual.
4. Apakah `createOrReplace` Silver dapat dibaca kembali & terkait di MinIO.
5. Perilaku churn session per tabel di mode cluster (waktu/overhead).

### Needs Design Review
1. Overwrite `createOrReplace` tanpa riwayat pada Silver (sudah didokumentasikan di Phase 3; konsisten namun perlu keputusan formal).
2. Apakah baris mahasiswa tanpa `tanggal_masuk` yang dibuang perlu dipertahankan/ditandai khusus (mis. status "data tidak lengkap") alih-alih dihapus — keputusan peneliti.
3. Memindahkan pemanggilan `get_spark` sekali di `process_all_tables` (passing shared session) untuk menghindari session churn — refactor kecil, **sedang tidak diubah** agar tidak mengubah perilaku tanpa verifikasi runtime.

---

## 13. Changes Made

| File | Masalah | Perubahan | Alasan |
|---|---|---|---|
| *(tidak ada file kode diubah)* | — | — | Tidak ditemukan bug/inkonsistensi yang dapat dibuktikan 100% statis pada Silver. Semua temuan tergantung runtime/data aktual atau merupakan keputusan desain. Per instruksi: **jika ragu, jangan ubah**. |

Dokumen ini (`docs/CODE_AUDIT_PHASE_04_SILVER.md`) adalah output audit.

---

## 14. Files Reviewed But Not Changed

- `backend/silver/silver.py` — inti audit (cleaning, validasi mahasiswa, write Iceberg)
- `backend/spark/session.py` — config session/catalog/namespace
- `backend/config/settings.py` — `ICEBERG_NAMESPACE`, `ICEBERG_CATALOG`, warehouse, MinIO creds
- `backend/utils/logger.py` — logging
- `backend/services/pipeline_service.py`, `backend/services/pipeline_runner.py`, `backend/services/pipeline_state.py` — pemanggil/status Silver
- `scripts/test_silver.py`, `scripts/cek_count.py` — script pemeriksa Silver
- `backend/gold/gold_mahasiswa.py`, `backend/gold/gold_prodi.py`, `backend/gold/gold_kurikulum.py`, `backend/gold/gold.py` — konsumen Silver (dibaca untuk kontrak schema & boundary, **tidak diubah**)
- `backend/feature_store/*` — konsumen Gold (hanya dibaca untuk boundary)
- `docs/ALUR_PENGERJAAN.md`, `docs/REVIEW_PROJECT.md` — dokumentasi alur
- `docs/CODE_AUDIT_PHASE_03_BRONZE.md` — konteks Bronze

---

## 15. Runtime Verification Checklist

> Tidak ada item yang dicentang; verifikasi dilakukan nanti di komputer lab (Docker menyala).

- [ ] Silver dapat membaca Bronze
- [ ] Cleaning berjalan
- [ ] Missing value handling sesuai
- [ ] Duplicate handling sesuai
- [ ] Date conversion benar
- [ ] Datatype benar
- [ ] Tidak ada data loss yang tidak disengaja
- [ ] Silver berhasil ditulis sebagai Iceberg
- [ ] Silver dapat dibaca kembali
- [ ] Silver tersimpan di MinIO