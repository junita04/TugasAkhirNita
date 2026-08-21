# RESUME TAHAP 4A — MINIO

## Tujuan

Mengarsipkan artefak penelitian Tahap 1–3 ke MinIO secara idempoten tanpa
mengubah feature engineering, model GaussianNB, local Iceberg warehouse, atau
pipeline yang sudah lulus.

## Kondisi Sebelum

MinIO sehat dan bucket `raw`, `warehouse`, `models`, serta `logs` sudah ada.
Dataset asli sudah berada di `raw`; artefak Iceberg, model v3, timing, dan
pipeline logs masih berada di filesystem lokal.

## Perubahan

- Menambahkan `scripts/validate_minio_artifacts.py`.
- Menambahkan `scripts/test_validate_minio_artifacts.py`.
- Manifest arsip menggunakan prefix berikut:
  - `warehouse/iceberg/{bronze,silver,gold,feature_store}`
  - `models/gaussian_nb/v3`
  - `logs/timing`
  - `logs/pipeline`
- Sync mendaftar object dengan `mc ls --recursive --json`, lalu hanya mengirim
  path yang belum ada. Tidak ada perintah penghapusan atau overwrite object.

## Hasil Sinkronisasi

Sync terakhir memeriksa 2.781 source files dan selesai dalam 11,72 detik.
Object yang sudah ada dilewati. Validasi raw mengunduh object sementara dan
membandingkan checksum SHA-256 dengan file lokal.

## Struktur Bucket dan Object

| Bucket | Object | Ukuran total |
|---|---:|---:|
| `raw` | 1 | 2.144.392 byte |
| `warehouse` | 2.708 | 10.773.513 byte |
| `models` | 4 | 253.109 byte |
| `logs` | 69 | 2.196.371 byte |

Jumlah object warehouse terdiri dari Bronze 1.820, Silver 430, Gold 190, dan
Feature Store 268. Logs terdiri dari 5 timing object dan 64 pipeline object.

## Hasil Validasi

```text
MINIO ARTIFACT VALIDATION
=========================
Raw Dataset             PASS
Bronze                  PASS
Silver                  PASS
Gold                    PASS
Feature Store           PASS
Model v3                PASS
Timing                  PASS
Pipeline Logs           PASS
Overall                 PASS
```

## Masalah yang Ditemukan dan Perbaikan

1. `Path.sep` tidak ada pada `pathlib.Path`; diperbaiki dengan `os.sep`.
2. Image MinIO tidak menyediakan Unix `find`; sinkronisasi dan validasi kini
   menggunakan `mc ls --recursive --json`.
3. Output satu baris per file membuat proses sulit diselesaikan lewat runner;
   output kini diringkas per kategori tanpa mengubah data yang dikirim.

## Batasan

Arsip MinIO mempertahankan local Iceberg warehouse sebagai source of truth
yang sudah tervalidasi. Tidak ada migrasi catalog, perubahan Spark/Airflow,
retraining model, atau penghapusan data pada Tahap 4A.

## File yang Diubah

- `scripts/validate_minio_artifacts.py`
- `scripts/test_validate_minio_artifacts.py`
- `docs/RESUME_TAHAP_4A_MINIO.md`

## Kesimpulan

Tahap 4A MinIO PASS. Object storage MinIO menyimpan raw dataset, arsip
Iceberg Bronze/Silver/Gold/Feature Store, GaussianNB v3, timing, dan pipeline
logs secara terstruktur. Siap untuk Tahap 4B.
