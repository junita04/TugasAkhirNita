# Academic Graduation Prediction System

Pipeline FastAPI ini memproses file Excel melalui Bronze, Silver, Gold, dan Feature Store menggunakan Apache Spark dan Apache Iceberg.

## Arsitektur

```text
Excel -> FastAPI -> Bronze -> Silver -> Gold Iceberg
                                |-> Trino (catalog iceberg, schema gold)
                                `-> Apache Superset

Gold -> PostgreSQL serving snapshot (kompatibilitas pipeline lama)
Superset metadata -> PostgreSQL database superset
```

Trino adalah sumber query analitik Superset. Superset tidak membaca tabel PostgreSQL serving. PostgreSQL serving tetap dipertahankan karena pipeline lama masih memanggil `publish_gold_tables()` setelah Gold dan sebelum Feature Store; Iceberg tetap menjadi source of truth.

Dataset Superset yang didaftarkan otomatis:

- `iceberg.gold.gold_mahasiswa`
- `iceberg.gold.gold_program_studi`
- `iceberg.gold.gold_kurikulum`

## Prasyarat

- Docker Desktop dengan Docker Compose aktif.
- Python 3.11 dan dependency pada `requirements.txt`.
- JDK yang sesuai untuk PySpark saat pipeline dijalankan di host Windows.

Siapkan environment:

```powershell
Copy-Item .env.example .env
```

Jangan commit `.env`; file tersebut berisi credential lokal. Gunakan `.env.example` sebagai template.

## Mode pipeline lokal

Mode lokal adalah default untuk FastAPI yang dijalankan dari host. Spark memakai `local[*]`, catalog Hadoop `local`, dan warehouse filesystem pada folder `iceberg/`.

```powershell
$env:SPARK_MODE = "local"
$env:SPARK_MASTER_URL = "local[*]"
$env:ICEBERG_CATALOG = "local"
$env:ICEBERG_WAREHOUSE = (Join-Path (Get-Location) "iceberg")
uvicorn main:app --reload
```

Upload Excel ke endpoint `POST /upload/`. Pipeline menjalankan:

```text
Excel -> Bronze -> Silver -> Gold -> PostgreSQL snapshot -> Feature Store
```

Jalur PostgreSQL tetap aktif untuk kompatibilitas, tetapi bukan sumber dataset Superset.

## Mode cluster Docker

Mode cluster memakai Spark Master Docker, Hive Metastore, dan warehouse Iceberg di MinIO.

```powershell
$env:SPARK_MODE = "cluster"
$env:SPARK_MASTER_URL = "spark://spark-master:7077"
$env:ICEBERG_CATALOG = "iceberg"
$env:ICEBERG_WAREHOUSE = "s3a://warehouse/iceberg"
docker compose up -d --build
docker compose ps
```

Superset menunggu PostgreSQL metadata, Redis, dan Trino sehat. Trino membaca catalog Iceberg melalui Hive Metastore dan MinIO. Buka:

- Superset: <http://localhost:8088>
- Trino: <http://localhost:8082>
- Spark Master UI: <http://localhost:8080>
- Spark History UI: <http://localhost:18080>
- MinIO Console: <http://localhost:9001>

Kredensial admin Superset berasal dari `SUPERSET_ADMIN_USERNAME`, `SUPERSET_ADMIN_EMAIL`, dan `SUPERSET_ADMIN_PASSWORD` di `.env`.

## Validasi

Validasi sintaks Compose tanpa menjalankan container:

```powershell
docker compose config
```

Jalankan test konfigurasi dan integrasi pipeline:

```powershell
python -m unittest scripts.test_spark_session scripts.test_superset_config scripts.test_compose_architecture scripts.test_pipeline_publish -v
```

Smoke test pembuatan SparkSession lokal, jika dependency Spark dan Java sudah tersedia:

```powershell
$env:RUN_SPARK_SMOKE = "1"
python scripts/test_spark_session.py
```

## Operasional

```powershell
# Status dan log bootstrap Superset
docker compose ps
docker compose logs -f superset-init

# Restart query UI dan worker
docker compose restart superset superset-worker

# Hentikan service, pertahankan volume
docker compose down

# Hapus volume database dan data lake; gunakan hanya jika reset total memang diinginkan
docker compose down -v
```

Jika koneksi Trino atau dataset belum muncul, periksa `docker compose logs trino` dan `docker compose logs superset-init`. Bootstrap idempotent dan akan mempertahankan dataset yang sudah ada berdasarkan database, schema, dan nama tabel.

Jika FastAPI berjalan di host, gunakan `POSTGRES_HOST=localhost` dan `POSTGRES_PORT=5432`. Jika nilai credential PostgreSQL diubah setelah volume dibuat, gunakan credential lama atau reset volume secara sadar.
