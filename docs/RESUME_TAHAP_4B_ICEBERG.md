# RESUME TAHAP 4B — AUDIT ICEBERG CATALOG & HIVE METASTORE

## Tujuan

Menentukan secara read-only mengapa object Iceberg yang telah diarsipkan ke
MinIO belum terlihat sebagai namespace/table melalui Spark + Hive Metastore.

## Environment

- Spark 3.5.3, Java 11.0.24
- Spark Master/Worker sehat; satu worker `ALIVE`
- Hive Metastore sehat pada `thrift://hive-metastore:9083`
- MinIO sehat pada `http://minio:9000`
- Network Docker: `lakehouse`
- Tidak ada rebuild, recreate, pipeline ETL, atau operasi mutasi.

## Konfigurasi Catalog Efektif

Konfigurasi yang dipakai Spark SQL smoke/audit:

```text
spark.sql.catalog.iceberg       = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.iceberg.type  = hive
spark.sql.catalog.iceberg.uri   = thrift://hive-metastore:9083
spark.sql.catalog.iceberg.warehouse = s3a://warehouse/iceberg
spark.hadoop.fs.s3a.endpoint    = http://minio:9000
spark.hadoop.fs.s3a.impl        = org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.path.style.access = true
spark.sql.extensions             = org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
```

Nilai access key/secret key tidak ditulis; Spark menandainya sebagai redacted
ketika `SET` ditampilkan.

## Hasil Hive Metastore

Perintah read-only:

```sql
SHOW NAMESPACES IN iceberg;
SHOW TABLES IN iceberg.default;
```

Hasil namespace hanya:

```text
default
```

`SHOW TABLES IN iceberg.default` dan `SHOW TABLES IN iceberg.bronze` tidak
menghasilkan table. PostgreSQL metastore berisi schema Hive Metastore, tetapi
tidak ada record tabel pipeline yang terlihat melalui catalog Spark.

Spark mengeluarkan warning bahwa schema version Hive belum tercatat, namun
tetap berhasil terhubung dan menjalankan query catalog.

## Hasil Iceberg dan MinIO

MinIO dapat dijangkau dan berisi 2.708 object pada `warehouse/iceberg`:

- Bronze: 1.820
- Silver: 430
- Gold: 190
- Feature Store: 268

Object mencakup metadata Iceberg valid seperti `metadata/*.metadata.json`,
`version-hint.text`, manifest Avro, manifest-list, dan data Parquet.

Contoh object MinIO:

```text
warehouse/iceberg/bronze/data_kelas/metadata/v1.metadata.json
warehouse/iceberg/bronze/data_kelas/metadata/version-hint.text
```

Local Iceberg juga memiliki struktur valid dan jumlah file sama dengan arsip
MinIO. Namun metadata lokal menyimpan location seperti:

```text
file:///D:/TA/TugasAkhirNita/iceberg/bronze/data_kelas
```

Dengan demikian, arsip object ke MinIO tidak otomatis mendaftarkan tabel ke
Hive Metastore dan tidak mengubah location metadata dari `file:///...` menjadi
`s3a://warehouse/iceberg/...`.

## Diagnosis

| Pemeriksaan | Hasil | Status |
|---|---|---|
| Spark catalog config | Hive catalog + S3A warehouse efektif | PASS |
| Hive Metastore connection | Spark SQL dapat terhubung | PASS |
| Namespace iceberg | Hanya `default` | FAIL |
| Namespace pipeline | Tidak ditemukan | FAIL |
| Existing Iceberg metadata | Valid di local dan object MinIO | PASS |
| MinIO warehouse reachable | 2.708 object dapat dilist | PASS |
| Local vs MinIO consistency | File terarsip, tetapi location metadata masih `file:///...` | FAIL |

## Root Cause Paling Mungkin

Pipeline Tahap 1–3 membuat tabel menggunakan Hadoop/local catalog pada
warehouse filesystem `file:///D:/TA/TugasAkhirNita/iceberg`. Tahap 4A menyalin
file Iceberg ke MinIO sebagai arsip, tetapi tidak melakukan registration ke
Hive Metastore dan tidak menulis ulang metadata location. Spark cluster
menggunakan catalog Hive yang berbeda, sehingga hanya namespace `default`
terlihat.

## Bukti Pendukung

1. Konfigurasi Spark efektif menunjuk ke `thrift://hive-metastore:9083` dan
   `s3a://warehouse/iceberg`.
2. `SHOW NAMESPACES IN iceberg` hanya mengembalikan `default`.
3. Local `v8.metadata.json` memiliki location `file:///D:/TA/...`.
4. MinIO berisi metadata Iceberg, tetapi object storage tidak otomatis mengisi
   database catalog Hive.
5. Tidak ada `UnsupportedClassVersionError`, kegagalan worker, atau error
   konektivitas Spark–Master.

## Yang Belum Terbukti

- Belum terbukti apakah semua metadata yang diarsipkan dapat dibaca langsung
  melalui `s3a://` karena metadata masih menunjuk ke `file:///`.
- Belum terbukti nama database/table Hive yang diinginkan untuk registrasi.
- Belum terbukti apakah pipeline Airflow cluster pernah berhasil membuat
  namespace/tabel Hive pada instance metastore ini.

## Opsi Perbaikan Paling Aman

1. **Registrasi ulang tabel secara eksplisit pada Hive Metastore** dengan
   location `s3a://warehouse/iceberg/...`, setelah memvalidasi metadata dan
   mapping table satu per satu. Risiko: perlu memastikan semua metadata/data
   file direferensikan dengan URI S3A yang benar.
2. **Jalankan ulang pipeline pada mode cluster** menggunakan catalog Hive dan
   warehouse MinIO untuk menghasilkan table registration native. Risiko: dapat
   menulis object baru dan harus dilakukan dengan guard/backup serta tanpa
   mengubah hasil Tahap 3.
3. **Pertahankan local catalog sebagai source of truth** dan gunakan MinIO
   hanya sebagai arsip. Risiko: Spark cluster tidak dapat membaca tabel melalui
   Hive Metastore sampai registration dilakukan.

Opsi 1 paling terkontrol, tetapi belum boleh diterapkan pada audit ini.

## Status Tahap 4B

`BLOCKED` pada smoke test catalog/table discovery. Spark, Hive Metastore, dan
MinIO reachable, tetapi namespace/table pipeline belum terdaftar pada Hive
Metastore yang digunakan Spark cluster.
