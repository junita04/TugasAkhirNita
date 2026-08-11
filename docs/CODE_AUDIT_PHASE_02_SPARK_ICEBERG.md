# Phase 2 — Spark & Iceberg Configuration Audit (Docker-Based)

Re-audit statis (tanpa menjalankan service) untuk **arsitektur Docker-based**:

> **"Integrasi Gold Layer Akademik ke Feature Store untuk Pengembangan Model Prediksi Tingkat Kelulusan Mahasiswa di Institut Teknologi Sumatera Berbasis Machine Learning"**

Project utama: `D:\TugasAkhirNita\`

---

## 0. Keputusan Arsitektur Final (Docker-Based)

1. Hanya Docker yang menyediakan layanan; `docker-compose.yml` adalah **sumber kebenaran** konfigurasi runtime.
2. **Spark DIJALANKAN SEUTUHNYA DI DALAM DOCKER** (`spark-master`, `spark-worker`, `spark-history`). Spark TIDAK dijalankan di host Windows. Mode `local` di host tidak dipakai untuk kebutuhan riset.
3. Client di dalam network `lakehouse` memakai service name; host Windows memakai port yang dipublish (`localhost`).
4. Konfigurasi/konstanta default sudah mengarah ke Docker (service names) kecuali di-override.
5. Arsitektur penelitian (alur Bronze → Silver → Gold → Feature Store → ML) tidak berubah.

---

## 1. Fokus Audit & Checklist

### 1.1 `docker-compose.yml` — Spark / MinIO / network

| Item | Status | Bukti |
|---|---|---|
| Network `lakehouse` tersedia | ✅ | `networks.lakehouse.driver: bridge` |
| Layanan `spark-master` | ✅ | image Spark 3.5.x + `command ... master.Master`, profile `[spark-docker]` |
| Layanan `spark-worker` | ✅ | worker mengarah `spark://spark-master:7077`, profile `[spark-docker]` |
| Layanan `spark-history` | ✅ | `SPARK_HISTORY_OPTS` → `file:/opt/bitnami/spark/logs` |
| Layanan `minio` | ✅ | endpoints `9000` (S3) & `9001` (console) |
| Layanan `hive-metastore` | ✅ | port `9083`, bergantung `postgres-hive` + `minio-init` |
| Semua service di network yang sama | ✅ | semua `networks: [lakehouse]` |

**Verdict:** tidak ada masalah jelas pada Compose → **tidak diubah**.

### 1.2 `backend/spark/session.py` — Docker-appropriateness

| Item | Status | Bukti |
|---|---|---|
| Master diambil dari `settings.MASTER` | ✅ | `session.py:94` `.master(MASTER)` |
| Endpoint S3A dari `settings.S3_ENDPOINT` | ✅ | `session.py:50` `fs.s3a.endpoint` |
| HMS dari `settings.HIVE_METASTORE_URI` | ✅ | `session.py:40` `catalog.uri` |
| Iceberg extension terpasang | ✅ | `session.py:109-112` `spark.sql.extensions` → `IcebergSparkSessionExtensions` |
| Jar Iceberg/Hadoop-AWS/AWS-SDK eksplisit | ✅ | `session.py:124-133` |
| Namespace dibikin sebelum tulis | ✅ | `session.py:173-176` `CREATE NAMESPACE IF NOT EXISTS` (`bronze`, `silver`, `gold`, `feature_store`) |
| Binding `127.0.0.1` hanya untuk mode `local` | ✅ | `session.py:154-159` guard `if SPARK_MODE == "local"` |

**Catatan portabel:** `SPARK_LOCAL_DIR = os.getenv("SPARK_LOCAL_DIRS", "spark-tmp")` relatif terhadap CWD. Di dalam container, path relatif bergantung direktori kerja proses; bukan bug statis, diverifikasi saat runtime.

### 1.3 Local paths (`D:\`, `C:\`, `/mnt/`, `localhost`, `127.0.0.1`, `file://`)

| Lokasi | Temuan | Keterangan |
|---|---|---|
| `backend/config/settings.py:26` | `SPARK_EVENT_DIR = PROJECT_ROOT / "spark-events"` | Path host. `SPARK_EVENT_LOG_DIR.as_uri()` → `file:///...` (host). Dipakai driver; pada cluster penuh di dalam container, direkomendasikan arahkan ke volume/shared path — verifikasi runtime. |
| `backend/spark/session.py:154-159` | `127.0.0.1` hanya pada mode `local` | Aman; mode cluster tidak memaksa loopback. |
| `.env` / `.env.example` | `localhost:9000`, `localhost:9083`, `local[*]` | **Diperbaiki** → service names (lihat §3). |
| `README.md` | dokumentasi mode `local` sebagai rekomendasi | Diperbarui mengikuti keputusan final (lihat §3). |
| `docs/ALUR_PENGERJAAN.md:79-80` | contoh `S3_ENDPOINT=http://localhost:9000` | Dokumen alur lama; dicatat, tidak mengubah kode. |

### 1.4 MinIO endpoint (`fs.s3a.endpoint`, `S3_ENDPOINT`)

KEPUTUSAN: Spark berjalan **di dalam network Docker**, sehingga harus memakai service name `http://minio:9000`, bukan `localhost:9000`.

| Sumber | Nilai baru | Konsisten |
|---|---|---|
| `backend/config/settings.py:71` (default) | `http://minio:9000` | ✅ |
| `backend/spark/session.py:50` | memakai `S3_ENDPOINT` | ✅ |
| `.env` | `http://minio:9000` (sebelumnya `localhost`) | ✅ **diperbaiki** |
| `.env.example` | `http://minio:9000` (sebelumnya `localhost`) | ✅ **diperbaiki** |
| `docker/trino/catalog/iceberg.properties:5` | `s3.endpoint=http://minio:9000` | ✅ |
| `docker/hive-metastore/hive-site.xml` | `minio:9000` | ✅ |

### 1.5 Iceberg warehouse (`spark.sql.catalog.*.warehouse`)

| Sumber | Nilai |
|---|---|
| `session.py:42` | `spark.sql.catalog.iceberg.warehouse = ICEBERG_WAREHOUSE` |
| `settings.py:65` (cluster default) | `s3a://warehouse/iceberg` |
| `.env` / `.env.example` | `s3a://warehouse/iceberg` |
| `docker/hive-metastore/hive-site.xml` | warehouse `s3a://warehouse/iceberg` (phase 1) |

**Verdict:** konsisten (bucket `warehouse` di MinIO).

### 1.6 Iceberg extension (`spark.sql.extensions`)

`session.py:109-112` sudah memuat:
```
spark.sql.extensions = org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
```
**Verdict:** ✅ terpasang (tidak diubah pada fase ini — sudah benar sejak perbaikan sebelumnya).

### 1.7 Catalog consistency

| Aspek | Nilai | Catatan |
|---|---|---|
| `ICEBERG_CATALOG` | `iceberg` | nama catalog produksi |
| `ICEBERG_NAMESPACE` | `= ICEBERG_CATALOG` | namespace aktif `iceberg` |
| Tipe catalog (cluster) | `hive` | HMS |
| HMS URI | `thrift://hive-metastore:9083` | service name |
| Namespace dibuat | `bronze`, `silver`, `gold`, `feature_store` | `session.py:173-176` |
| Trino catalog | `iceberg` (HIVE_METASTORE) | `docker/trino/catalog/iceberg.properties` |

**Verdict:** konsisten. Tidak ada referensi literal `local.` di kode produksi Bronze/Silver/Gold/Feature Store/Serving (sudah diganti ke `ICEBERG_NAMESPACE` pada fase 1).

### 1.8 Dependencies (PySpark · Iceberg · Hadoop-AWS · AWS-SDK)

| Dependensi | Spark session (`session.py`) | Spark Dockerfile | Konsisten |
|---|---|---|---|
| PySpark / image Spark | `pyspark==3.5.3` (requirements) | `apache/spark:3.5.2` | ⚠️ minor (3.5.3 vs 3.5.2) |
| Iceberg runtime | `iceberg-spark-runtime-3.5_2.12:1.5.2` | `iceberg-spark-runtime-3.5_2.12-1.5.2.jar` | ✅ |
| PostgreSQL JDBC | `postgresql:42.7.4` | `postgresql-42.7.4.jar` | ✅ |
| Hadoop-AWS | `hadoop-aws:3.3.4` | `hadoop-aws-3.3.4.jar` | ✅ |
| AWS SDK | `aws-java-sdk-bundle:1.12.261` | `aws-java-sdk-bundle-1.12.261.jar` | ✅ |
| Commons Pool2 | (via Spark) | `commons-pool2-2.11.1.jar` | ✅ |

> ⚠️ Versi minor PySpark (3.5.3) vs image Spark (3.5.2): hanya rekomendasi menyamakan; tidak berdampak statis pada konfigurasi.

---

## 2. Findings (Docker-Based)

### Critical
- Tidak ada temuan Critical.

### High
- Tidak ada temuan High yang dapat dibuktikan murni statis.

### Medium
1. **Mode `local` masih terdokumentasi sebagai rekomendasi** — `README.md` (section "Mode ringan: Spark lokal") dan plan `2026-08-03-lightweight-local-spark-architecture.md` memuat alur Spark lokal di Windows, bertentangan dengan keputusan final. → **README diperbarui** ke mode utama Docker-based; plan lama dicatat sebagai superseded (tidak diubah).
2. **`SPARK_EVENT_LOG_DIR` menunjuk path host** (`PROJECT_ROOT / "spark-events"`, URI `file:///`). Pada cluster penuh dalam container, driver perlu path yang ada di container/volume bersama. Verifikasi runtime; jika driver berjalan di host (client mode), path host tetap valid.

### Low
3. `docs/ALUR_PENGERJAAN.md:79-80` masih mencontohkan `S3_ENDPOINT=http://localhost:9000` dan `HIVE_METASTORE_URI=thrift://localhost:9083`. Dokumentasi alur kerja lama; tidak mengubah kode.
4. `SPARK_LOCAL_DIRS` (`spark-tmp`) bersifat relatif-CWD; di container perlu dipastikan writable (verifikasi runtime).

### Needs Runtime Verification
1. Driver & executor di dalam container dapat mencapai `minio:9000`, `hive-metastore:9083`, dan `spark://spark-master:7077`.
2. Kesesuaian versi minor PySpark 3.5.3 vs image Spark 3.5.2 saat `RUN_SPARK_SMOKE`.
3. Event log dir (`spark-events`) terhadap lokasi running driver (host vs container).
4. `SPARK_JARS_EXTRA` (`/opt/bitnami/spark/jars/extra`) terdeteksi oleh `spark-submit` dari dalam image Spark Docker.

---

## 3. Docker-Based Spark Architecture (Ringkasan)

```text
Host Windows (FastAPI / Airflow DAG trigger)

            |  HTTP / spark-submit ke hostname docker (spark-master)
            v
     ┌────────────────  network: lakehouse  ────────────────┐
     │   spark-master :7077   ('cluster' driver+executor)   │
     │   spark-worker :7077         │                       │
     │   spark-history :18080       │                       │
     │        │                     │                       │
     │        v                     v                       │
     │   hive-metastore :9083 ── postgres-hive :5433        │
     │   minio :9000 (s3a://warehouse/iceberg)              │
     │   trino :8082 (catalog iceberg → HMS + MinIO)        │
     │   superset :8088 (via Trino) / postgres :5432        │
     └──────────────────────────────────────────────────────┘
```

Konfigurasi aktif (SPARK_MODE=cluster):

| Konstanta | Nilai | Asal |
|---|---|---|
| `SPARK_MODE` | `cluster` | `.env` |
| `SPARK_MASTER_URL` | `spark://spark-master:7077` | `.env` / default cluster `settings.py` |
| `ICEBERG_CATALOG` | `iceberg` | `.env` / default cluster |
| `ICEBERG_WAREHOUSE` | `s3a://warehouse/iceberg` | `.env` / default cluster |
| `S3_ENDPOINT` | `http://minio:9000` | `.env` / default `settings.py` |
| `HIVE_METASTORE_URI` | `thrift://hive-metastore:9083` | `.env` / default `settings.py` |

> Catatan deployment: bila driver berjalan **di host Windows** dalam mode client, service name di atas tidak bisa di-resolve dari host — gunakan port terpublish (`localhost`) untuk sisi driver dan pastikan konfigurasi executor tetap memakai service name. Bila seluruh Spark berjalan di container (target audit ini), service name berlaku untuk semua.

---

## 4. Docker Runtime Verification Checklist

Berikutnya, verifikasi saat seluruh stack Docker menyala (bukan statis):

- [ ] `docker compose config` sukses.
- [ ] `docker compose up --profile spark-docker -d` → `spark-master`, `spark-worker`, `spark-history` sehat.
- [ ] MinIO healthy & `mc ready local` sukses; bucket `warehouse`, `raw`, `models`, `logs` ada.
- [ ] `hive-metastore` healthy (`nc -z localhost 9083`), `trino` healthy, `superset` dan `superset-init` berhasil bootstrap dataset `gold`.
- [ ] Spark dapat membuat namespace `iceberg.bronze|silver|gold|feature_store` (cek `session.py`).
- [ ] Pipeline `SPARK_MODE=cluster` berhasil: Bronze → Silver → Gold → `publish_gold_tables` → Feature Store.
- [ ] `publish_gold_tables()` menulis ke PostgreSQL (host `localhost:5432` bila driver di host; service `postgres:5432` bila driver di container).
- [ ] Superset membaca `iceberg.gold.*` melalui Trino.
- [ ] Event log (`spark-events`) & History UI (`:18080`) menampilkan aplikasi.
- [ ] Spark History UI membaca log yang dihasilkan driver (sesuaikan `SPARK_EVENT_LOG_DIR` bila driver di container).

---

## 5. Files Changed (Fase Ini)

| File | Masalah | Perubahan | Alasan |
|---|---|---|---|
| `.env` | `S3_ENDPOINT=http://localhost:9000`, `HIVE_METASTORE_URI=thrift://localhost:9083`, `SPARK_MODE=local`, `SPARK_MASTER_URL=local[*]` | `S3_ENDPOINT=http://minio:9000`, `HIVE_METASTORE_URI=thrift://hive-metastore:9083`, `SPARK_MODE=cluster`, `SPARK_MASTER_URL=spark://spark-master:7077` | Konsisten dengan keputusan Spark penuh di Docker |
| `.env.example` | mendokumentasikan mode local sebagai contoh | default & komentar diarahkan ke `cluster` + service names | Template mencerminkan arsitektur target |
| `scripts/test_compose_architecture.py` | menguji `.env.example` memuat `SPARK_MODE=local` | menguji `SPARK_MODE=cluster`, `SPARK_MASTER_URL=spark://spark-master:7077`, `S3_ENDPOINT=http://minio:9000`, `HIVE_METASTORE_URI=thrift://hive-metastore:9083` | Menjaga tes konsisten dgn keputusan final |
| `README.md` | merekomendasikan Spark lokal Windows | mode utama diarahkan ke Spark Docker + catatan service names | Dokumentasi mengikuti arsitektur final |

## 6. Files Reviewed But Not Changed

- `docker-compose.yml` (Spark/MinIO/HMS/network sudah konsisten)
- `backend/config/settings.py` (default sudah Docker-friendly)
- `backend/spark/session.py` (sudah sesuai; guard `127.0.0.1` hanya mode local)
- `backend/serving/postgres_sink.py`, `backend/services/*`
- `docker/spark/Dockerfile`, `docker/trino/catalog/iceberg.properties`,
  `docker/hive-metastore/hive-site.xml`
- `docs/ALUR_PENGERJAAN.md`, `docs/superpowers/plans/2026-08-03-lightweight-local-spark-architecture.md` (superseded, dicatat)

---

## 7. Issues That Must Be Checked Later

1. Verifikasi runtime seluruh endpoint service name saat stack `lakehouse` aktif (checklist §4).
2. Keputusan lokasi event log driver (host vs container) → sesuaikan `SPARK_EVENT_LOG_DIR`.
3. Menyamakan versi PySpark (3.5.3) dengan image Spark Docker (3.5.2) bila diperlukan.
4. Memigrasikan dokumentasi alur lama (`ALUR_PENGERJAAN.md`, plan lightweight-local-spark) ke arsitektur Docker-based.
5. Bila driver berjalan di host dalam mode client: dokumentasi endpoint split (localhost untuk driver, service name untuk executor) agar tidak menimbulkan kebingungan runtime.