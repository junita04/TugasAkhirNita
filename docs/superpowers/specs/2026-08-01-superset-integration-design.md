# Desain Integrasi Apache Superset

## Tujuan

Menghubungkan pipeline FastAPI yang menghasilkan tabel Gold berbasis Apache Iceberg ke Apache Superset melalui PostgreSQL sebagai serving layer analitik. Superset dijalankan melalui Docker Compose dan dapat membaca data Gold setelah pipeline selesai.

## Ruang Lingkup

- Menyediakan PostgreSQL, Redis, Superset web, Superset worker, dan proses inisialisasi Superset melalui Docker Compose.
- Menambahkan konfigurasi koneksi PostgreSQL yang aman melalui environment variables.
- Menyalin tabel Gold berikut ke PostgreSQL setelah proses Gold selesai:
  - `gold_mahasiswa`
  - `gold_program_studi`
  - `gold_kurikulum`
- Mendaftarkan PostgreSQL dan dataset tersebut ke Superset secara otomatis.
- Menambahkan dokumentasi menjalankan aplikasi, Superset, dan alur refresh data.

Di luar ruang lingkup: pembuatan dashboard/chart bisnis final, orkestrasi produksi, autentikasi pengguna tingkat lanjut, dan penggantian Iceberg sebagai sumber data utama.

## Arsitektur

```text
Excel
  -> FastAPI upload endpoint
  -> Bronze -> Silver -> Gold (Apache Iceberg)
  -> PostgreSQL serving tables
  -> Apache Superset datasets/charts
```

Iceberg tetap menjadi sumber data utama pipeline. PostgreSQL hanya menyajikan snapshot terbaru untuk kebutuhan query Superset. Proses publish dilakukan setelah seluruh tabel Gold berhasil dibuat, sehingga dashboard tidak membaca hasil Gold yang belum lengkap.

## Komponen

### Serving sink

Modul baru bertanggung jawab mengubah Spark DataFrame Gold menjadi tabel PostgreSQL dengan JDBC. Penulisan menggunakan mode overwrite agar upload terbaru menggantikan snapshot sebelumnya. Nama tabel dan schema PostgreSQL bersifat eksplisit dan tidak berasal langsung dari input pengguna.

Konfigurasi minimal:

- host PostgreSQL
- port PostgreSQL
- database
- username
- password
- schema serving

Spark diberi dependency PostgreSQL JDBC melalui konfigurasi session yang sudah digunakan aplikasi.

### Integrasi pipeline

`run_pipeline()` menjalankan publish ke PostgreSQL setelah seluruh tahap Gold selesai dan sebelum `run_feature_store()`. Publish harus mengembalikan error yang jelas jika PostgreSQL tidak dapat dijangkau. Kegagalan publish tidak menghapus data Iceberg yang sudah berhasil dibuat.

### Docker Compose

Compose menyediakan:

- PostgreSQL untuk data serving dan metadata aplikasi Superset
- Redis untuk broker/cache Superset
- Superset init untuk migrasi database, pembuatan admin, dan inisialisasi konfigurasi
- Superset web untuk UI
- Superset worker untuk pekerjaan asynchronous

Port PostgreSQL diekspos ke host agar FastAPI yang berjalan lokal dapat menulis data. Superset menggunakan nama service Docker untuk koneksi internal.

### Inisialisasi Superset

Script init yang idempotent akan:

1. menjalankan upgrade database metadata Superset;
2. membuat user admin jika belum ada;
3. memuat konfigurasi database serving;
4. membuat database connection dan dataset Gold jika belum ada.

Password admin dan database dibaca dari `.env`, dengan `.env.example` sebagai template tanpa secret nyata.

## Error handling

- Validasi konfigurasi environment dilakukan saat aplikasi mulai atau saat sink dipanggil.
- Error koneksi PostgreSQL dicatat dengan host/database tanpa mencetak password.
- Kegagalan publish menghasilkan kegagalan pipeline yang eksplisit agar pengguna mengetahui dashboard belum diperbarui.
- Penulisan tabel dilakukan satu per satu dengan nama tabel yang tetap; implementasi tidak menjalankan SQL dari input bebas pengguna.

## Verifikasi

- Unit test untuk pembentukan JDBC URL/properties dan pemetaan tabel Gold ke tabel PostgreSQL.
- Test pipeline dengan sink dimock agar alur publish dipastikan dipanggil setelah tahap transformasi.
- Validasi konfigurasi Compose.
- Smoke test: jalankan stack, buka Superset, pastikan koneksi PostgreSQL dan tiga dataset tersedia.
- Smoke test upload Excel: pastikan row count tabel serving berubah sesuai data Gold terbaru.

## Kriteria Sukses

- `docker compose up` dapat menyiapkan Superset dan dependensinya.
- FastAPI dapat terhubung ke PostgreSQL melalui konfigurasi `.env`.
- Setelah upload Excel berhasil, tiga tabel Gold tersedia di PostgreSQL.
- Superset dapat melakukan query terhadap ketiga dataset tanpa akses langsung ke filesystem Iceberg.
- Setup dan troubleshooting dasar terdokumentasi di README.
