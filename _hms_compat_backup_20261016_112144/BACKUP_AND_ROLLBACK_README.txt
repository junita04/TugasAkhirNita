========================================================================
BACKUP & ROLLBACK — Remediasi Hive Metastore (4.2.1 -> 3.1.3)
Direktori: _hms_compat_backup_20261016_112144\
Dibuat  : 2026-10-16
STATUS  : PERSIAPAN SAJA. Tidak ada perubahan pada produksi.
========================================================================

------------------------------------------------------------
1. ARTEFAK BACKUP & CHECKSUMS
------------------------------------------------------------
Lihat CHECKSUMS.txt (SHA256). Ringkas:

  metastore_dump.sql                     176,870 B   (pg_dump logis, skema 4.2.0, 63 tabel)
  inventory_63.csv                        14,430 B   (63 tabel: db,tbl,sd_location,metadata_location)
  manifest_63.json                        47,197 B   (63 tabel + rows + snapshot_id + kategori lokasi)
  prod_before_snapshot.json                7,590 B   (rows + snapshot_id SEBELUM)
  prod_after_snapshot.json                 7,590 B   (rows + snapshot_id SESUDAH; identik dgn before)
  metadata_keys_55.txt                     5,052 B   (55 key metadata.json tabel s3://)
  db_volume_backup\postgres-hive-data_20261016.tar.gz  12,545,828 B  (backup level-VOLUME PGDATA metastore)
  trino_local_warehouse\                  404 file  (4,635,307 B)  salinan 8 tabel warehouse lokal Trino
  hive-metastore_src\                     sumber Dockerfile/entrypoint/hive-site/init.sql SEBELUM perubahan
  isolated_test\                          hasil uji terisolasi (skema 4.2.0 vs 3.1.0)

Backup TUNABLE (dibuat saat persiapan, bukan di produksi):
  MinIO bucket  hive-backup-20261016\gold.db\...   404 objek / 4,635,307 B (byte-identical dgn Trino)

------------------------------------------------------------
2. CARA RESTORE / VERIFIKASI BACKUP (sudah DIUJI)
------------------------------------------------------------
2a. pg_dump  (logis, konsisten) — RESTORE SUDAH DIUJI:
      docker cp metastore_dump.sql <pg>:/tmp/dump.sql
      psql -U hive -d postgres -c 'CREATE DATABASE restore_test OWNER hive;'
      psql -U hive -d restore_test -f /tmp/dump.sql
      # HASIL UJI: SCHEMA_VERSION=4.2.0, 63 TBLS, 9 DBS, 63 ICEBERG, nama tabel identik.

2b. Volume PGDATA — RESTORE SUDAH DIUJI:
      docker volume create hmsvol-restore
      docker run --rm -v hmsvol-restore:/data -v "<backup>\db_volume_backup:/b:ro" postgres:16-alpine \
             sh -c "tar xzf /b/postgres-hive-data_20261016.tar.gz -C /data"
      docker run -d --name pgvol-restore -e POSTGRES_HOST_AUTH_METHOD=trust \
             -v hmsvol-restore:/var/lib/postgresql/data postgres:16-alpine
      psql -U hive -d metastore -c 'SELECT "SCHEMA_VERSION" FROM "VERSION";'   # 4.2.0
      psql -U hive -d metastore -c 'SELECT count(*) FROM "TBLS";'               # 63
      # HASIL UJI: SKEMA 4.2.0, 63 tabel terbaca. Backup volume VALID.

2c. Warehouse lokal Trino (8 tabel file:) — KOPI SUDAH DIVERIFIKASI:
      container : 404 file, 4,774,571 B (du termasuk direktori) / 4,635,307 B berkas
      host      : 404 file, 4,635,307 B  -> IDENTIK (per-dir: 16,16,304,16,12,12,12,16)
      MinIO     : bucket hive-backup-20261016 -> 404 objek, Total Size 4,635,307 B -> IDENTIK
      spot SHA256 metadata.json (model_metrics v2) container == MinIO:
      07c8e92d7f6b66672c40b946efa80743e4070ea2847a2fa0bd1675c2e3e58f8e

2d. Objek metadata 55 tabel s3:// — DIVERIFIKASI ADA:
      head-object untuk 55 metadata_object_key: OK=55 MISSING=0

------------------------------------------------------------
3. CATATAN PENTING — 8 TABEL file: (RISIKO UTAMA)
------------------------------------------------------------
Isi metadata.json (dan manifest avro) 8 tabel gold_model_a MENYIMPAN PATH ABSOLUT
`file:/opt/hive/data/warehouse/gold.db/<table>-<uuid>/...` (field `location`, manifest-list,
snapshot manifest, dan stats). Konsekuensi:
  - Data+metadata sudah AMAN disalin (host + MinIO), tetapi SALINAN itu TIDAK BISA langsung
    dibaca dari MinIO tanpa rewrite, karena manifest menunjuk path `file:` (bukan s3a://).
  - Registrasi ulang biasa (register_table) dengan lokasi MinIO akan tetap menunjuk `file:`.
  - Data asli hanya hidup di layer container Trino (ephemeral). Jangan recreate/rebuild
    container Trino tanpa lebih dulu mengamankan/memigrasi tabel ini.
METODE MIGRASI YANG BENAR (dijalankan pada FASE EKSEKUSI, setelah disetujui):
  Opsi A (disarankan): set `iceberg.catalog.warehouse=s3a://warehouse/iceberg` pada
     docker/trino/catalog/iceberg.properties, lalu buat ulang tabel di MinIO via
     CTAS:  CREATE TABLE iceberg.gold.<t> WITH (...) AS SELECT * FROM iceberg.gold.<t>;
     (menulis ulang data+metadata ke s3a), lalu drop tabel file: lama.
     -> Menghasilkan metadata baru yang menunjuk s3a:// (durable).
  Opsi B: regenerate 8 tabel dari sumber (pipeline/model output) setelah HMS diperbaiki.
  Opsi C: rewrite metadata (bukan string-replace; harus via Iceberg rewrite/expire).

------------------------------------------------------------
4. PROSEDUR ROLLBACK PRODUKSI (bila remediasi gagal)
------------------------------------------------------------
Prasyarat: jendela sepi; DAG produksi & QA tetap paused.

  R1. Hentikan layanan terkait:
        docker compose stop hive-metastore trino

  R2. Pulihkan database metastore — pilih salah satu:
      (a) Level-volume (paling cepat):
            docker run --rm -v academic-datalakehouse_postgres-hive-data:/data \
                   -v "<backup>\db_volume_backup:/b:ro" postgres:16-alpine \
                   sh -c "rm -rf /data/* && tar xzf /b/postgres-hive-data_20261016.tar.gz -C /data"
      (b) Logis (pg_dump):
            docker compose up -d postgres-hive
            docker exec <pg> psql -U hive -d postgres -c 'DROP DATABASE metastore;'
            docker exec <pg> psql -U hive -d postgres -c 'CREATE DATABASE metastore OWNER hive;'
            docker cp metastore_dump.sql <pg>:/tmp/dump.sql
            docker exec <pg> psql -U hive -d metastore -f /tmp/dump.sql

  R3. Kembalikan Definisi HMS ke 4.2.1:
        - pulihkan docker/hive-metastore/Dockerfile dari hive-metastore_src\
        - docker compose up -d --build hive-metastore

  R4. Pulihkan warehouse lokal Trino (bila Trino terlanjur di-recreate):
        docker cp "<backup>\trino_local_warehouse\." <trino>:/opt/hive/data/warehouse/
        # atau dari MinIO bucket hive-backup-20261016

  R5. Hidupkan kembali:
        docker compose up -d trino hive-metastore

  R6. Verifikasi rollback:
        - SCHEMA_VERSION=4.2.0, 63 TBLS (psql)
        - Trino: SHOW TABLES per skema (bronze/silver/gold/feature_store)
        - bandingkan qa_prod_signature vs prod_before_snapshot.json (rows + snapshot_id)
        - Superset: refresh + uji chart kunci

------------------------------------------------------------
5. PRA-SYARAT SEBELUM EKSEKUSI (checklist)
------------------------------------------------------------
  [x] pg_dump tervalidasi restore
  [x] volume backup tervalidasi restore
  [x] warehouse lokal Trino ter-backup (host + MinIO, byte-identical)
  [x] 55 metadata objek s3 diverifikasi ada
  [x] manifest 63 tabel lengkap (rows + snapshot_id)
  [x] 8 tabel file: dipetakan + metode migrasi ditentukan
  [ ] PERSETUJUAN eksplisit untuk mengubah produksi (HMS/skema/registrasi)
  [ ] Jendela downtime disetujui
  [ ] Keputusan opsi migrasi 8 tabel (A/B/C)
========================================================================
