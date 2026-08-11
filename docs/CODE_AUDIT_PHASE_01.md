# Phase 1 — Project Structure & Configuration Audit

Audit statis (tanpa menjalankan aplikasi/service) pada project Tugas Akhir:

> **"Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis Machine Learning"**

Project utama: `D:\TugasAkhirNita\`

---

## 1. Project Structure

```
D:\TugasAkhirNita\
├── main.py                          # Entry point FastAPI (4 router: upload, train, predict, pipeline)
├── requirements.txt                 # Dependency Python utama
├── docker-compose.yml               # Orchestrasi seluruh service lakehouse (local/docker)
├── .env                             # Konfigurasi runtime lokal (di-gitignore)
├── .env.example                     # Template konfigurasi yang boleh di-commit
├── .gitignore
├── README.md
├── AGENTS.md
├── struktur_project.txt             # Output `tree` lama (arti-status file saja, bukan konfigurasi)
├── skills-lock.json                 # Lockfile skill find-skills
├── .agents/
│   └── skills/find-skills/SKILL.md
├── .worktrees/superset-integration/ # Worktree git (branch feature/superset-integration) — BUKAN sumber kebenaran
├── backend/
│   ├── api/                         # FastAPI router: upload, train, predict, pipeline
│   ├── config/settings.py           # Pusat konfigurasi + loader .env
│   ├── bronze/                      # Layer Bronze (Spark + Iceberg)
│   ├── silver/                      # Layer Silver
│   ├── gold/                        # Layer Gold (gold_mahasiswa, gold_prodi, gold_kurikulum)
│   ├── feature_store/               # Training & inference dataset
│   ├── ml/                          # data_preparation, train, evaluate, predict, registry
│   ├── services/                    # pipeline_service, pipeline_runner, prediction_service, dll.
│   ├── serving/postgres_sink.py     # Publish Gold -> PostgreSQL
│   ├── spark/session.py             # Pembuat SparkSession + konfigurasi Iceberg catalog
│   └── utils/                       # excel_utils, file_utils, logger
├── docker/
│   ├── airflow/                     # Dockerfile + DAG prediction_pipeline
│   ├── hive-metastore/              # Dockerfile + hive-site.xml
│   ├── minio/                       # Dockerfile + init.sh (bucket + seed data)
│   ├── postgres/init.sql            # Buat DB superset
│   ├── spark/                       # Dockerfile Spark Master/Worker/History
│   ├── superset/                    # Dockerfile, superset_config, trino_config, register_datasets
│   └── trino/                        # config.properties, node.properties, catalog/iceberg.properties
├── scripts/                         # Test & utility: test_*, cek_*, check_*
├── data/req_data_rut.xlsx           # Dataset asli
├── iceberg/                         # Warehouse Iceberg lokal (mode local catalog)
├── models/                          # Model registry + metadata
├── logs/                            # Log runtime
├── spark-events/ spark-tmp/ static/ # Artefak runtime
└── docs/                            # Dokumentasi & rencana
```

### Entry point & source code utama

| Item | Lokasi |
|---|---|
| Entry point aplikasi | `main.py` — `uvicorn main:app` |
| Konfigurasi sentral | `backend/config/settings.py` |
| Orkestrasi pipeline | `backend/services/pipeline_service.py` |
| Spark + Iceberg session | `backend/spark/session.py` |
| Sink Gold->PostgreSQL | `backend/serving/postgres_sink.py` |

---

## 2. Main Project vs Worktree

- **Project utama**: `D:\TugasAkhirNita\` pada branch `master` (commit `a653295`).
- **Worktree**: `D:\TugasAkhirNita\.worktrees\superset-integration\` pada branch `feature/superset-integration` (commit `96bfea8`). Terdaftar resmi via `git worktree list`.

Perbedaan penting yang **tidak boleh dicampur**:

| Aspek | Utama (master) | Worktree (feature/superset-integration) |
|---|---|---|
| `docker-compose.yml` | Kaya: postgres, redis, minio, hive, spark, trino, airflow, superset + profiles | Hanya postgres + redis + superset (versi awal) |
| `backend/api` | upload, train, predict, pipeline | upload, train, predict, dashboard (masih ada `dashboard.py`) |
| `requirements.txt` | `pyspark==3.5.3` | `pyspark==4.2.0` |
| `.env.example` | Lengkap (>90 baris) | Singkat (~11 baris) |
| `docker/superset` | register_datasets via Trino, ada `trino_config.py` | register_datasets via PostgreSQL serving |

Tidak ada referensi silang antar kedua area; `backend/config/settings.py` menghitung `PROJECT_ROOT` berdasar `Path(__file__)`, sehingga isolates. `.gitignore` sudah meng-ignore `.worktrees/`. **Tidak dilakukan penyalinan/penggabungan.**

---

## 3. Main Configuration Files

| File | Peran |
|---|---|
| `requirements.txt` | 28 paket pinned. Inti: fastapi, uvicorn, pyspark 3.5.3, pandas, numpy, pyarrow, scikit-learn, openpyxl, python-multipart |
| `.env` | Runtime lokal (gitignored): Postgres serving, Superset, MinIO/S3, Hive Metastore, Spark, Trino, Airflow |
| `.env.example` | Template yang aman di-commit |
| `docker-compose.yml` | Service + profiles (`spark-docker`, `trino`, `airflow`, `superset`, `superset-worker`) |
| `backend/config/settings.py` | Load .env, default koneksi, definisi direktori project |
| `docker/spark/Dockerfile` | Spark 3.5 Docker dengan extra jars (Iceberg, Postgres JDBC, Hadoop-AWS) |
| `docker/hive-metastore/hive-site.xml` | HMS -> Postgres `postgres-hive`, warehouse `s3a://warehouse/iceberg`, S3 endpoint `minio:9000` |
| `docker/trino/catalog/iceberg.properties` | Catalog Trino -> HMS + MinIO (native S3) |
| `docker/superset/superset_config.py` | Metadata Superset -> Postgres, Celery broker -> Redis |
| `docker/airflow/dags/prediction_pipeline.py` | DAG orkestrasi harian |
| `skills-lock.json` | Lockfile skill |
| `main.py` | FastAPI app + router |

Tidak ditemukan `pyproject.toml`, `setup.cfg`, `.ini`, atau file `*.json` konfigurasi aplikasi lain di project utama.

---

## 4. Dependencies

### Python (`requirements.txt`) — project utama
- Web: `fastapi==0.140.13`, `starlette==1.3.1`, `uvicorn==0.52.0`, `python-multipart==0.0.20`
- Data/ML: `pyspark==3.5.3`, `pandas==3.0.5`, `numpy==2.4.6`, `pyarrow==25.0.0`, `scikit-learn==1.9.0`, `scipy==1.17.1`, `joblib==1.5.3`, `openpyxl==3.1.5`, `narwhals==2.24.0`
- Utilitas: `pydantic==2.13.4`, `pydantic_core==2.46.4`, `py4j==0.10.9.7`, `python-dateutil`, `click`, `idna`, `anyio`, dll.

Catatan: versi pinned (mis. `numpy 2.4.6`, `pandas 3.0.5`, `starlette 1.3.1`) adalah versi yang sangat baru/lain dari biasanya; bukan masalah struktur, tetapi diverifikasi saat runtime nanti.

### Jars Spark (diunduh otomatis, `session.py`)
- `org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2`
- `com.crealytics:spark-excel_2.12:3.5.1_0.20.4`
- `org.postgresql:postgresql:42.7.4`
- `org.apache.hadoop:hadoop-aws:3.3.4`
- `com.amazonaws:aws-java-sdk-bundle:1.12.261`

### Docker (image)
- postgres:16-alpine, redis:7-alpine, minio/minio, minio/mc, apache/hive:3.1.3, apache/spark:3.5.2, trinodb/trino:462, apache/airflow:2.10.4-python3.11, apache/superset:6.0.0

---

## 5. Path & Environment Configuration

### Konfigurasi inti `backend/config/settings.py`
- `PROJECT_ROOT` dihitung dari lokasi file → portabel (bukan hardcode path).
- Direktori: `DATA_DIR`, `ICEBERG_DIR`, `MODEL_DIR`, `LOG_DIR`, `SPARK_EVENT_DIR`, `SCRIPT_DIR`, `STATIC_DIR` — semuanya relatif ke `PROJECT_ROOT`.
- Koneksi (default, dioverride `.env`):
  - S3: `S3_ENDPOINT=http://minio:9000` (default) vs `.env: http://localhost:9000` → konsisten untuk mode local.
  - HMS: `HIVE_METASTORE_URI=thrift://hive-metastore:9083` (default) vs `.env: localhost:9083`.
  - Postgres: `localhost:5432` (sesuai host FastAPI).
- `SPARK_MODE`: `local` (`.env`) dengan `MASTER=local[*]`.

### Temuan pada hardcoded / relatif path
1. **`backend/api/pipeline.py`** memakai `DATA_DIR` dari settings (benar, PROJECT_ROOT-anchored).
2. **`backend/api/upload.py`** sebelumnya memakai `Path("data")` (relatif ke CWD) → **diubah** ke `DATA_DIR` (lihat §7).
3. **`backend/services/prediction_service.py`** sebelumnya `MODEL_PATH = Path("models")/gaussian_nb` (CWD-relatif) → **diubah** ke `MODEL_DIR`.
4. **`backend/services/batch_prediction_service.py`** sebelumnya `Path("data")` & `Path("models")` → **diubah** ke `DATA_DIR`/`MODEL_DIR`.
5. **`backend/ml/registry.py`** masih `MODEL_DIR = "models"` (string CWD-relatif). Tidak disentuh karena masuk scope audit ML (phase berikut), tetapi dicatat §6.
6. **`backend/ml/predict.py`** masih `MODEL_PATH = "models/gaussian_nb"` (CWD-relatif). Sama, dicatat.
7. **`scripts/test_spark_session.py`** memanggil `_iceberg_configs` dengan `ICEBERG_WAREHOUSE="D:/data/iceberg"` — path absolut Windows hanya untuk simulasi unit test (mock), bukan konfigurasi produksi.
8. `.env` memakai `localhost` untuk S3/HMS/Postgres (mode local), sementara `docker-compose.yml` & file Docker memakai hostname service (`minio`, `hive-metastore`, `postgres`). Konfigurasi **sengaja split** antara host (Windows) & container (Docker) — konsisten dengan README mode "lightweight local Spark".

### Port yang dipakai
- `5432` Postgres serving, `5433` Postgres HMS, `5434` Postgres Airflow
- `9000` MinIO S3, `9001` MinIO console
- `9083` Hive Metastore thrift
- `8080` Spark master UI, `8081` worker, `7077` master, `18080` history
- `8082` Trino, `8088` Superset, `8085` Airflow webserver
- FastAPI host: `8000` (diasumsikan; DAG Airflow memanggil `host.docker.internal:8000`)

Semua port **tidak saling bertabrakan**. Perlu verifikasi runtime bahwa port 8000 dipakai FastAPI saat dijalankan bersama Airflow.

### Credential placeholder
- `.env`: password lokal (mis. `academic-local-password`).
- `.env.example`: `change-me`, `change-this-secret-key`.
- `docker/hive-metastore/hive-site.xml`: `minioadmin`/`minioadmin-password` di-hardcode (sesuai default minio). Ini duplikasi kredensial di file repo — harus konsisten dengan `.env`.
- `docker/trino/catalog/iceberg.properties`: `minioadmin`/`minioadmin-password` ikut di-hardcode. Sama dengan di atas.
- `.env` adalah file lokal dan sudah di-gitignore (aman).

---

## 6. Findings

### Critical
- Tidak ada temuan Critical pada scope struktur/konfigurasi.

### High
- Tidak ada temuan High yang dapat dibuktikan murni statis pada phase ini.

### Medium
1. **Path CWD-relatif tidak konsisten** — `upload.py`, `prediction_service.py`, `batch_prediction_service.py` memakai `Path("data")`/`Path("models")` relatif ke CWD sedangkan `pipeline.py` & `settings.py` memakai `PROJECT_ROOT`. Jika proses dijalankan dari direktori berbeda (mis. `cd scripts; python -m uvicorn main:app`), file upload/model akan tertulis di lokasi salah. → **Diperbaiki** (lihat §7).
2. **Duplikasi kredensial MinIO di file repo** — `minioadmin`/`minioadmin-password` muncul di `.env`, `hive-site.xml`, dan `iceberg.properties`. Risiko drift bila password diganti.
3. **Versi Spark berbeda sumber** — `requirements.txt` pin `pyspark==3.5.3` sedangkan `docker/spark/Dockerfile` memakai image `apache/spark:3.5.2`; extra jars Iceberg untuk Spark `3.5_2.12`. Perlu disamakan/diverifikasi saat runtime.

### Low
4. `static/` kosong dan `STATIC_DIR` di settings tidak terpakai setelah penghapusan frontend — artefak sisa yang tidak berbahaya.
5. `struktur_project.txt` adalah dump `tree` lama, tidak lagi sepenuhnya akurat.
6. `backend/api/pipeline.py` menyisakan endpoint `/pipeline/state` & `/pipeline/start` yang memakai `pipeline_state`/`pipeline_runner` (masih ada) — tidak error, hanya tidak dipakai halaman.

### Needs Runtime Verification
1. Pencapaian `minio`, `hive-metastore`, `postgres`, dsb. dari host Windows `localhost` saat service Docker aktif.
2. Kesesuaian versi paket Python pinned vs yang ter-install (`pyspark 3.5.3` vs ter-install; `pyarrow`, `scikit-learn`).
3. DAG Airflow memanggil `http://host.docker.internal:8000/pipeline/run` — FastAPI harus listen di port 8000 pada host.
4. Bootstrap Superset (`superset-init`) ↔ Trino ↔ HMS ↔ MinIO health order.
5. Endpoint `/pipeline/run` dengan `SPARK_MODE=local` yang menarik jar via Maven (memerlukan koneksi internet pertama kali).

---

## 7. Changes Made

| File | Masalah | Perubahan | Alasan |
|---|---|---|---|
| `backend/api/upload.py` | `UPLOAD_DIR = Path("data")` relatif CWD | `UPLOAD_DIR = DATA_DIR` (import dari settings) | Menyamakan dengan `pipeline.py`; menghilangkan ketergantungan direktori kerja |
| `backend/services/prediction_service.py` | `MODEL_PATH = Path("models")/gaussian_nb` relatif CWD | `MODEL_PATH = MODEL_DIR / "gaussian_nb"` | Memakai `MODEL_DIR` (PROJECT_ROOT/models) seperti settings |
| `backend/services/batch_prediction_service.py` | `UPLOAD_DIR = Path("data")`, `MODEL_PATH = Path("models")/gaussian_nb` | `UPLOAD_DIR = DATA_DIR`, `MODEL_PATH = MODEL_DIR / "gaussian_nb"` | Konsistensi path terhadap PROJECT_ROOT |

Semua perubahan bersifat mekanis (mengganti konstanta path relatif-ke-CWD dengan konstanta PROJECT_ROOT-anchored dari `settings.py`) dan tidak mengubah runnable-path ketika aplikasi dijalankan dari root project.

`backend/ml/registry.py` & `backend/ml/predict.py` TIDAK diubah (masuk scope audit ML).

---

## 8. Files Reviewed But Not Changed

- `main.py`
- `requirements.txt`
- `.env`, `.env.example`, `.gitignore`, `README.md`, `AGENTS.md`, `skills-lock.json`
- `docker-compose.yml`
- `backend/config/settings.py`
- `backend/spark/session.py`
- `backend/api/pipeline.py`, `backend/serving/postgres_sink.py`
- `backend/services/pipeline_service.py`, `pipeline_runner.py`, `pipeline_state.py`, `history_service.py`
- `backend/utils/*.py`
- Seluruh `docker/**` (Dockerfile, hive-site.xml, trino, superset, airflow DAG, minio init)
- Seluruh `scripts/*.py`
- `.worktrees/superset-integration/` (dibandingkan, tidak diubah)
- `docs/**`

---

## 9. Issues That Must Be Checked Later

Berikutnya (phase audit berikutnya) — implementasi & runtime:
1. Runtime Spark: pembuatan namespace + tabel Iceberg di HMS/MinIO untuk Bronze/Silver/Gold/Feature Store.
2. Koneksi JDBC `publish_gold_tables()` ke Postgres (5432), khususnya mode overwrite & SCHEMA `public`.
3. Konsistensi path model di `backend/ml/registry.py` & `backend/ml/predict.py` terhadap `MODEL_DIR`.
4. Kesesuaian versi PySpark/Java di host dengan extra jars Spark Docker (Iceberg 1.5.2, Hadoop-AWS 3.3.4).
5. Verifikasi seluruh port & `host.docker.internal` saat seluruh stack Docker menyala.
6. Duplikasi kredensial MinIO (hive-site.xml, iceberg.properties, .env) — usul dipindah ke variabel env bila memungkinkan.