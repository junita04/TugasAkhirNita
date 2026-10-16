#!/usr/bin/env python3
"""STAGING - Registrasi metadata tabel Iceberg ke Hive Metastore baru.

Tujuan
------
Mendaftarkan ulang tabel Iceberg yang datanya SUDAH ADA (di MinIO) ke
HMS baru (3.1.3 + skema 3.1.0) memakai prosedur Iceberg
`system.register_table`. Prosedur ini HANYA menunjuk ke metadata.json yang
sudah ada:
  - TIDAK menulis ulang data,
  - TIDAK membuat snapshot baru,
  - TIDAK mengubah metadata.json.
Jadi `snapshot_id` dan jumlah baris tabel produksi tetap sama.

Batas aman
----------
- Skrip ini TIDAK dijalankan otomatis. Default = --dry-run (hanya cetak SQL).
- Hanya mendaftarkan tabel berkategori `s3_minio`. Tabel `file_trino_local`
  HARUS dimigrasi lebih dulu (lihat migrate_file_tables.py).

Contoh
------
  # Lihat rencana (tanpa koneksi apa pun):
  python register_tables.py --manifest .../manifest_63.json --dry-run

  # Eksekusi (di dalam airflow-scheduler, HMS baru sudah up):
  python register_tables.py --manifest .../manifest_63.json \
      --hms-uri thrift://hive-metastore:9083 \
      --warehouse s3a://warehouse/iceberg --execute --verify
"""
import argparse
import json
import sys


def load_tables(manifest_path, categories, only):
    with open(manifest_path, "r", encoding="utf-8-sig") as fh:
        manifest = json.load(fh)
    tables = manifest["tables"] if isinstance(manifest, dict) else manifest
    selected = [t for t in tables if t["category"] in categories]
    if only:
        wanted = set(only)
        selected = [t for t in selected if f"{t['db']}.{t['tbl']}" in wanted]
    return selected


def build_spark(hms_uri, warehouse, jars_dir):
    import os
    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder
        .appName("staging-register-tables")
        .master(os.getenv("SPARK_MASTER", "local[*]"))
        .config("spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.hive_iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.hive_iceberg.type", "hive")
        .config("spark.sql.catalog.hive_iceberg.uri", hms_uri)
        .config("spark.sql.catalog.hive_iceberg.warehouse", warehouse)
        .config("spark.sql.catalog.hive_iceberg.cache-enabled", "false")
        # MinIO / S3A (data + metadata bisa berskema s3a:// maupun s3://)
        .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT", "http://minio:9000"))
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("S3_ACCESS_KEY", "minioadmin"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("S3_SECRET_KEY", "minioadmin-password"))
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    )
    if jars_dir and os.path.isdir(jars_dir):
        builder = (builder
                   .config("spark.driver.extraClassPath", f"{jars_dir}/*")
                   .config("spark.executor.extraClassPath", f"{jars_dir}/*"))
    return builder.getOrCreate()


def register_sql(t):
    return (f"CALL hive_iceberg.system.register_table("
            f"table => '{t['db']}.{t['tbl']}', "
            f"metadata_file => '{t['metadata_location']}')")


def verify_table(spark, t):
    fq = f"hive_iceberg.{t['db']}.{t['tbl']}"
    rows = spark.sql(f"SELECT count(*) AS c FROM {fq}").collect()[0]["c"]
    snap = spark.sql(
        f"SELECT snapshot_id FROM {fq}.snapshots ORDER BY committed_at DESC LIMIT 1"
    ).collect()
    snap_id = str(snap[0]["snapshot_id"]) if snap else None
    return rows, snap_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--hms-uri", default="thrift://hive-metastore:9083")
    ap.add_argument("--warehouse", default="s3a://warehouse/iceberg")
    ap.add_argument("--jars-dir", default="/opt/airflow/jars")
    ap.add_argument("--categories", default="s3_minio",
                    help="kategori yang didaftarkan (default: s3_minio)")
    ap.add_argument("--tables", default="",
                    help="batasi ke daftar db.tbl (dipisah koma)")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", dest="dry_run", action="store_false")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    categories = {c.strip() for c in args.categories.split(",") if c.strip()}
    only = [t.strip() for t in args.tables.split(",") if t.strip()]
    tables = load_tables(args.manifest, categories, only)

    print("=" * 72)
    print(f"mode       : {'DRY-RUN' if args.dry_run else 'EXECUTE'}")
    print(f"hms-uri    : {args.hms_uri}")
    print(f"warehouse  : {args.warehouse}")
    print(f"categories : {sorted(categories)}")
    print(f"tabel      : {len(tables)}")
    print("=" * 72)

    if args.dry_run:
        for t in tables:
            print(f"CREATE NAMESPACE IF NOT EXISTS hive_iceberg.{t['db']};")
            print(register_sql(t) + ";")
        print(f"\n[dry-run] {len(tables)} tabel siap didaftarkan (tidak dieksekusi).")
        return 0

    spark = build_spark(args.hms_uri, args.warehouse, args.jars_dir)
    failures = []
    for t in tables:
        fq = f"{t['db']}.{t['tbl']}"
        try:
            if spark.catalog.tableExists(f"hive_iceberg.{fq}"):
                print(f"[SKIP] {fq} sudah terdaftar (tidak disentuh).")
                continue
            spark.sql(f"CREATE NAMESPACE IF NOT EXISTS hive_iceberg.{t['db']}")
            spark.sql(register_sql(t))
            line = f"[OK]   registered {fq}"
            if args.verify:
                rows, snap = verify_table(spark, t)
                ok = (int(rows) == int(t["rows"])) and (
                    snap is None or str(snap) == str(t["snapshot_id"]))
                line += f" | rows={rows} (exp {t['rows']}) snapshot={snap} (exp {t['snapshot_id']})"
                if not ok:
                    failures.append(fq)
                    line = "[MISMATCH] " + line
            print(line)
        except Exception as exc:  # noqa: BLE001
            failures.append(fq)
            print(f"[FAIL] {fq}: {type(exc).__name__}: {exc}")

    print("=" * 72)
    if failures:
        print(f"SELESAI dengan {len(failures)} masalah: {failures}")
        return 1
    print(f"SELESAI: {len(tables)} tabel terdaftar & terverifikasi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
