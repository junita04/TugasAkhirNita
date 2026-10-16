# STAGING — Remediasi Hive Metastore (HMS 4.2.1 -> 3.1.3) + Migrasi 8 Tabel `file:`

> **STATUS: STAGING ONLY. TIDAK ADA yang diterapkan.**
> Direktori ini tidak direferensikan oleh `docker-compose.yml`
> (compose memakai context `./docker/hive-metastore`), sehingga **tidak
> otomatis diterapkan**. Semua perubahan produksi mensyaratkan persetujuan
> eksplisit.

## 1. Tujuan
1. Menurunkan HMS dari `apache/hive:standalone-metastore-4.2.1` ke `apache/hive:3.1.3`
   agar kompatibel dengan klien Hive 2.3.9 milik Spark 3.5.3.
2. Memakai **skema 3.1.0 baru** di DB **baru** (`metastore313`) **tanpa menghapus
   atau menimpa** DB `metastore` (4.2.0) yang aktif.
3. Mendaftarkan ulang 63 tabel Iceberg lewat `register_table` (metadata-only).
4. Memigrasikan 8 tabel `file:` (data hanya di container Trino) ke MinIO permanen.

## 2. Isi staging
| File | Fungsi |
|---|---|
| `Dockerfile` | Usulan HMS 3.1.3 (hadoop-aws 3.1.0, aws-sdk-bundle 1.11.375, pg 42.7.4) |
| `hive-site.xml` | Usulan konfigurasi → DB `metastore313` |
| `entrypoint.sh` | Identik dengan produksi (substitusi `${env:VAR}`) |
| `scripts/register_tables.py` | Registrasi metadata-only + verifikasi (default dry-run) |
| `scripts/migrate_file_tables.py` | CTAS 8 tabel + validasi rows & content-hash (default dry-run) |
| `scripts/validate_tables.py` | Bandingkan rows + snapshot_id vs `manifest_63.json` |
| `scripts/_trino_client.py` | Klien REST Trino (stdlib) |

## 3. Prasyarat
- Backup terverifikasi: `_hms_compat_backup_20261016_112144\` (+ `CHECKSUMS.txt`).
- `manifest_63.json` (55 `s3_minio` + 8 `file_trino_local`).
- Layanan produksi sehat; `superset-worker` unhealthy (pra-eksisting, tidak terkait).
- **Jangan** membuat ulang container `trino` sebelum migrasi 8 tabel selesai.

## 4. Urutan perintah (BELUM dijalankan — butuh persetujuan)

### Langkah A — Migrasi 8 tabel `file:` (SEBELUM ganti HMS)
Dijalankan saat HMS lama masih hidup, Trino masih memegang data `file:`.
```
# rencana (aman):
python _staging_hms313_20261016/scripts/migrate_file_tables.py \
    --manifest _hms_compat_backup_20261016_112144/manifest_63.json --dry-run

# eksekusi CTAS + validasi (nama target: <tbl>_perm):
python _staging_hms313_20261016/scripts/migrate_file_tables.py \
    --manifest _hms_compat_backup_20261016_112144/manifest_63.json \
    --trino-url http://localhost:8082 --execute
```
Dampak: **menambah** 8 tabel baru `gold.<tbl>_perm` di MinIO (s3://warehouse/iceberg).
Tidak mengubah/menghapus tabel sumber. Rename ke nama asli (`--rename`) BARU
dilakukan setelah validasi lulus dan persetujuan terpisah.

### Langkah B — DB metastore baru + HMS 3.1.3
```
# B1. buat DB baru (non-destruktif; `metastore` lama dibiarkan):
docker exec academic-datalakehouse-postgres-hive-1 \
    psql -U <POSTGRES_HIVE_USER> -c "CREATE DATABASE metastore313;"

# B2. staging -> aktif (perubahan produksi; butuh persetujuan):
#     salin Dockerfile, hive-site.xml, entrypoint.sh dari staging ke
#     docker/hive-metastore/  (BACKUP dulu isi lama)

# B3. run pertama IS_RESUME=false untuk inisialisasi skema 3.1.0:
docker compose build hive-metastore
docker compose up -d hive-metastore          # dengan IS_RESUME=false (sekali)

# B4. setelah skema 3.1.0 terbentuk, kembalikan IS_RESUME=true lalu:
docker compose up -d hive-metastore
```
Dampak: HMS sementara berhenti singkat; Trino/Superset kehilangan visibilitas
sampai registrasi ulang selesai. DB lama `metastore` TIDAK tersentuh.

### Langkah C — Registrasi ulang 63 tabel ke HMS baru
```
python _staging_hms313_20261016/scripts/register_tables.py \
    --manifest _hms_compat_backup_20261016_112144/manifest_63.json \
    --hms-uri thrift://hive-metastore:9083 --warehouse s3a://warehouse/iceberg \
    --execute --verify
```
`register_table` hanya menunjuk metadata.json yang ada: **tidak menulis ulang
data, tidak membuat snapshot baru.** Setelah Langkah C, daftarkan juga 8 tabel
hasil migrasi (kategori `s3_minio` bila sudah di-rename, atau `--tables ...`).

### Langkah D — Validasi
```
python _staging_hms313_20261016/scripts/validate_tables.py \
    --manifest _hms_compat_backup_20261016_112144/manifest_63.json \
    --trino-url http://localhost:8082
```
Sukses bila: seluruh 55 tabel `s3_minio` rows + snapshot_id sama; 8 tabel
`file:` rows sama.

## 5. Rencana migrasi 8 tabel `file:` — detail & validasi
Untuk setiap tabel T: **BEFORE** (rows + md5 atas semua kolom terurut) →
**CTAS** ke `gold.T_perm` → **AFTER** (rows + md5) → **LULUS** bila sama
persis. Kegagalan tidak menghentikan tabel lain dan salinan dibiarkan untuk
inspeksi. `snapshot_id` tabel `file:` memang akan berubah (tabel baru) — itu
wajar; yang dijaga adalah **isinya**.

| Tabel sumber | rows |
|---|---|
| `gold.classification_report_model_a` | 3 |
| `gold.confusion_matrix_model_a` | 4 |
| `gold.inference_result_model_a_utama` | 12338 |
| `gold.model_metrics_model_a` | 1 |
| `gold.model_predictions_model_a` | 12338 |
| `gold.prediction_by_angkatan_model_a` | 3 |
| `gold.training_label_distribution_by_angkatan` | 17 |
| `gold.training_label_distribution_model_a` | 2 |

## 6. Rollback
| Perubahan | Rollback |
|---|---|
| Migrasi 8 tabel | `DROP TABLE iceberg.gold.<tbl>_perm;` (sumber `file:` tetap utuh) |
| HMS 3.1.3 | kembalikan `docker/hive-metastore/{Dockerfile,hive-site.xml}` ke versi lama, `docker compose build hive-metastore && docker compose up -d` |
| DB | DB lama `metastore` tidak pernah diubah → cukup arahkan `ConnectionURL` kembali ke `metastore` |
| Registrasi | tidak ada data yang diubah, tidak perlu rollback khusus |

## 7. Kriteria sukses
- `qa_full_pipeline` selesai sampai `iceberg.qa_gold.inference_result_model_a_utama`.
- 63 tabel produksi cocok dengan `manifest_63.json` (rows; snapshot_id untuk s3).
- Trino & Superset kembali normal.

## 8. Catatan
- Jalur ini memakai `register_table` sehingga `snapshot_id` tidak berubah.
- Celah `fs.s3.impl` di `backend/spark/session.py` bersifat terpisah dan tidak
  dipakai jalur pipeline (pipeline menulis tabel `s3a` baru); dapat ditambah
  belakangan bila ingin Spark membaca tabel ber-meta `s3://`.
