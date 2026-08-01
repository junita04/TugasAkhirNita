# Desain Arsitektur Spark Environment-Driven dan Superset via Trino

## Tujuan

Menyelesaikan transisi arsitektur data lakehouse agar satu pipeline dapat dijalankan dalam dua mode runtime—lokal dan cluster—serta Apache Superset membaca tabel Gold melalui Trino, bukan melalui PostgreSQL serving.

PostgreSQL serving dan `publish_gold_tables()` tetap dipertahankan untuk kompatibilitas pipeline yang sudah ada. PostgreSQL tidak lagi menjadi sumber dataset analitik utama Superset.

## Ruang Lingkup

- Menormalkan konfigurasi Spark berbasis environment untuk mode `local` dan `cluster`.
- Memastikan mode lokal memakai Spark standalone lokal dan warehouse filesystem.
- Memastikan mode cluster memakai Spark Master Docker, Hive Metastore, dan warehouse MinIO/S3A.
- Mengubah koneksi dataset Superset dari PostgreSQL serving menjadi Trino.
- Mendaftarkan tiga tabel Gold yang sama secara idempotent melalui koneksi Trino.
- Memperbarui `.env.example` dan README dengan arsitektur, operasi, dan validasi terbaru.
- Memvalidasi konfigurasi Compose dan pipeline lokal.

Di luar ruang lingkup: menghapus PostgreSQL serving, mengubah transformasi Bronze/Silver/Gold, membuat dashboard bisnis baru, atau menambah orkestrasi produksi.

## Arsitektur

```text
Excel
  -> FastAPI
  -> Bronze -> Silver -> Gold
  -> Iceberg catalog
       |-- local mode: filesystem warehouse `iceberg/`
       `-- cluster mode: Hive Metastore + MinIO warehouse
  -> Trino (catalog iceberg, schema gold)
  -> Apache Superset datasets/charts

Gold -> PostgreSQL serving snapshot (kompatibilitas pipeline lama)
Superset metadata -> PostgreSQL metadata database
```

Trino menjadi jalur query analitik resmi Superset. PostgreSQL serving boleh tetap diperbarui oleh pipeline, tetapi dataset Superset tidak menggunakan tabel PostgreSQL tersebut.

## Konfigurasi Spark

`backend/config/settings.py` membaca `.env` lalu environment process dengan environment process sebagai prioritas. Nilai mode dinormalisasi dan hanya menerima `local` atau `cluster`.

- `SPARK_MODE=local` menggunakan `SPARK_MASTER_URL` bila diberikan, dengan default `local[*]`; driver bind/host diarahkan ke loopback; catalog default `local`; warehouse default ke folder `iceberg/` proyek.
- `SPARK_MODE=cluster` menggunakan `SPARK_MASTER_URL` bila diberikan, dengan default `spark://spark-master:7077`; driver tidak dipaksa bind ke loopback; catalog default `iceberg`; warehouse default `s3a://warehouse/iceberg`; Hive Metastore dan kredensial S3A dibaca dari environment.
- Explicit environment values tetap dapat override default profil, sehingga konfigurasi cluster eksternal tidak bergantung pada nama service Docker.
- Dependency Iceberg, spark-excel, dan PostgreSQL JDBC tetap dipasang oleh Spark session karena sink PostgreSQL masih dipertahankan.

Konfigurasi session tidak boleh membuat koneksi jaringan atau mengharuskan Spark hidup ketika modul konfigurasi diimpor. Fungsi konfigurasi yang dapat diuji secara unit dipisahkan dari pembuatan `SparkSession` bila diperlukan.

## Integrasi Superset dan Trino

Superset metadata tetap menggunakan PostgreSQL `superset`. Image Superset memasang driver SQLAlchemy Trino yang sesuai dengan versi Python/image yang dipakai.

Bootstrap Superset membuat atau memperbarui satu koneksi stabil bernama `Academic Trino` dengan URI internal Docker yang setara dengan:

```text
trino://trino@trino:8082/iceberg
```

Dataset yang didaftarkan tetap:

- schema `gold`, table `gold_mahasiswa`;
- schema `gold`, table `gold_program_studi`;
- schema `gold`, table `gold_kurikulum`.

Registrasi aman dijalankan berulang kali: koneksi dicari berdasarkan nama stabil, dan dataset dicari berdasarkan database, schema, serta table. Kredensial tidak ditulis ke log.

Superset init bergantung pada PostgreSQL metadata, Redis, dan Trino sehat sebelum migrasi, pembuatan admin, serta registrasi dataset. `docker compose config` harus dapat merender seluruh environment tanpa secret hard-coded di source selain default development yang sudah ada di `.env.example`.

## Kompatibilitas PostgreSQL

`publish_gold_tables()` tetap dipanggil setelah Gold selesai dan sebelum Feature Store. Sink ini tidak menjadi bagian dari koneksi dataset Superset. Perubahan baru tidak boleh menghapus tabel, konfigurasi, atau dependency yang diperlukan pipeline lokal untuk menulis snapshot PostgreSQL.

## Dokumentasi dan validasi

README menjelaskan:

1. pembuatan `.env` dari `.env.example`;
2. mode lokal FastAPI dan mode cluster Docker;
3. aliran data baru Iceberg → Trino → Superset;
4. peran PostgreSQL yang tersisa;
5. URL layanan utama dan perintah operasi;
6. `docker compose config` sebagai validasi konfigurasi;
7. test pipeline lokal dan batasan bahwa pipeline lokal memerlukan dependensi Spark yang sesuai.

Verifikasi implementasi mencakup unit test konfigurasi mode Spark dan target Trino, seluruh test Python yang relevan, `docker compose config`, serta smoke check pipeline lokal yang tidak memerlukan Superset membaca PostgreSQL.

## Kriteria Sukses

- Konfigurasi `SPARK_MODE=local` menghasilkan master dan catalog lokal yang benar.
- Konfigurasi `SPARK_MODE=cluster` menghasilkan master Spark Docker dan catalog Hive/MinIO yang benar.
- Superset mendaftarkan database Trino, bukan database PostgreSQL serving, sebagai sumber tiga dataset Gold.
- `docker compose config` berhasil.
- Test pipeline lokal yang relevan tetap berhasil atau kegagalan yang tersisa dapat dijelaskan sebagai dependensi eksternal yang belum aktif.
- README mencerminkan arsitektur dan prosedur operasi baru.
