# Academic Graduation Prediction System

Pipeline FastAPI ini memproses file Excel melalui Bronze, Silver, Gold, dan Feature Store. Tabel Gold dipublikasikan ke PostgreSQL agar dapat dianalisis melalui Apache Superset.

## Menjalankan Superset

Prasyarat: Docker Desktop dengan Docker Compose aktif.

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps
```

Buka Superset di <http://localhost:8088>. Username, email, dan password admin berasal dari `.env` (`SUPERSET_ADMIN_USERNAME`, `SUPERSET_ADMIN_EMAIL`, dan `SUPERSET_ADMIN_PASSWORD`).

Stack menyediakan PostgreSQL di `localhost:5432`, Redis, Superset web, Superset worker, dan proses inisialisasi. Database serving bernama `academic_serving`; metadata Superset disimpan di database `superset`. Koneksi dan dataset `gold_mahasiswa`, `gold_program_studi`, serta `gold_kurikulum` didaftarkan otomatis.

## Menjalankan FastAPI

Pastikan `.env` sudah ada agar konfigurasi PostgreSQL sama dengan Compose, lalu jalankan:

```powershell
uvicorn main:app --reload
```

Upload Excel ke endpoint `POST /upload/`. Pipeline akan menjalankan:

```text
Excel -> Bronze -> Silver -> Gold (Iceberg) -> PostgreSQL -> Superset
                                      \-> Feature Store
```

Setiap upload yang berhasil akan mengganti snapshot tiga tabel serving PostgreSQL. Iceberg tetap menjadi sumber data utama pipeline.

## Operasional

```powershell
# Lihat status dan log
docker compose ps
docker compose logs -f superset-init

# Restart UI/worker
docker compose restart superset superset-worker

# Hentikan service tetapi pertahankan volume database
docker compose down

# Hentikan service dan hapus data metadata/serving
docker compose down -v
```

Jangan menjalankan `docker compose down -v` jika data PostgreSQL masih diperlukan. Jangan commit `.env`; gunakan `.env.example` sebagai template.

## Troubleshooting

- Jika FastAPI tidak bisa tersambung, pastikan PostgreSQL container sehat dan `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432` saat FastAPI berjalan di host.
- Jika Superset belum tersedia, periksa `docker compose logs superset-init`; inisialisasi harus selesai sebelum service web dan worker berjalan.
- Jika password diubah setelah volume PostgreSQL dibuat, gunakan kredensial lama atau reset volume secara sadar dengan `docker compose down -v`.
