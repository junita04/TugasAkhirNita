#!/usr/bin/env python3
"""STAGING - Rencana & eksekusi migrasi 8 tabel `file:` (lokal Trino) ke
penyimpanan permanen di MinIO (s3://warehouse/iceberg), berbasis Trino.

Latar
-----
8 tabel gold menyimpan data HANYA di writable-layer container Trino
(`file:/opt/hive/data/warehouse/gold.db/...`). Bila container Trino dibuat
ulang, tabel-tabel ini HILANG. Trino sendiri sudah bisa membaca
`file:` (sumbernya) DAN menulis ke `s3a://` (core-site.xml memetakan s3/s3a),
sehingga CTAS lewat Trino adalah jalur paling aman.

Strategi (Opsi A)
-----------------
Untuk setiap tabel T (kategori `file_trino_local`):
  1. BEFORE : hitung jumlah baris + hash isi tabel sumber `iceberg.gold.T`.
  2. CTAS   : CREATE TABLE iceberg.gold.<T>_perm AS SELECT * FROM iceberg.gold.T
              (menulis data permanen ke s3, metadata baru).
  3. AFTER  : hitung jumlah baris + hash isi tabel baru.
  4. VALIDASI: rows_after == rows_before DAN hash_after == hash_before.
  5. RENAME : (langkah persetujuan terpisah) DROP tabel sumber `file:` lalu
              ALTER TABLE ..._perm RENAME TO T agar nama tetap sama.

Hash isi = md5(array_join(array_agg(row ORDER BY row), chr(10))) atas seluruh
kolom yang di-CAST ke varchar, sehingga tidak bergantung urutan baris.

Batas aman
----------
- Default --dry-run: TIDAK menyentuh Trino sama sekali, hanya mencetak SQL.
- Tidak pernah DROP/DELETE tabel sumber. Rename hanya jika --rename disertakan.
- Jalankan di lingkungan yang bisa menjangkau Trino (host:8082 atau container).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _trino_client import TrinoClient  # noqa: E402


SENTINEL = "\\N"


def load_file_tables(manifest_path, only):
    with open(manifest_path, "r", encoding="utf-8-sig") as fh:
        manifest = json.load(fh)
    tables = manifest["tables"] if isinstance(manifest, dict) else manifest
    sel = [t for t in tables if t["category"] == "file_trino_local"]
    if only:
        wanted = set(only)
        sel = [t for t in sel if f"{t['db']}.{t['tbl']}" in wanted]
    return sel


def columns_sql(db, tbl):
    return (
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{db}' AND table_name = '{tbl}' "
        "ORDER BY ordinal_position"
    )


def signature_sql(db, tbl, cols):
    exprs = ", ".join(
        f"coalesce(CAST(\"{c}\" AS varchar), '{SENTINEL}')" for c in cols
    )
    return (
        "SELECT count(*) AS n, "
        "md5(to_utf8(array_join(array_agg(r ORDER BY r), chr(10)))) AS h "
        f"FROM (SELECT concat_ws('|', {exprs}) AS r FROM {db}.\"{tbl}\")"
    )


def ctas_sql(db, src, dst, base):
    # Penting: location HARUS eksplisit ke S3. Tanpa ini Trino memakai
    # default location schema (file:/opt/hive/data/warehouse/...) sehingga
    # salinan tetap berada di layer lokal Trino (tidak permanen).
    loc = f"{base.rstrip('/')}/{db}.db/{dst}"
    return (f'CREATE TABLE {db}."{dst}" '
            f"WITH (location = '{loc}') AS SELECT * FROM {db}.\"{src}\"")


def fetch_signature(client, db, tbl):
    cols = [r[0] for r in client.query(columns_sql(db, tbl))[1]]
    cols = [c[0] if isinstance(c, list) else c for c in cols]
    sql = signature_sql(db, tbl, cols)
    _, rows = client.query(sql)
    n, h = rows[0]
    return int(n), h, cols, sql


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--trino-url", default="http://localhost:8082")
    ap.add_argument("--catalog", default="iceberg")
    ap.add_argument("--suffix", default="_perm")
    ap.add_argument("--target-base", default="s3://warehouse/iceberg",
                    help="basis lokasi S3 tujuan (default s3://warehouse/iceberg)")
    ap.add_argument("--tables", default="")
    ap.add_argument("--rename", action="store_true",
                    help="setelah validasi sukses: DROP sumber + RENAME _perm -> nama asli")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", dest="dry_run", action="store_false")
    args = ap.parse_args()

    only = [t.strip() for t in args.tables.split(",") if t.strip()]
    tables = load_file_tables(args.manifest, only)

    print("=" * 72)
    print(f"mode    : {'DRY-RUN' if args.dry_run else 'EXECUTE'}")
    print(f"trino   : {args.trino_url}")
    print(f"catalog : {args.catalog}")
    print(f"suffix  : {args.suffix}   rename={'ya' if args.rename else 'tidak'}")
    print(f"target  : {args.target_base}/<db>.db/<tbl>_perm")
    print(f"tabel   : {len(tables)}")
    print("=" * 72)

    client = None if args.dry_run else TrinoClient(url=args.trino_url,
                                                   catalog=args.catalog, schema="gold")

    results = []
    for t in tables:
        db, tbl = t["db"], t["tbl"]
        dst = tbl + args.suffix
        print("\n" + "-" * 72)
        print(f"TABEL {db}.{tbl}  (rows tercatat={t['rows']})")

        if args.dry_run:
            print(f"  [1] BEFORE : {signature_sql(db, tbl, ['<kolom...>'])}")
            print(f"  [2] CTAS   : {ctas_sql(db, tbl, dst, args.target_base)};")
            print(f"  [3] AFTER  : {signature_sql(db, dst, ['<kolom...>'])}")
            print(f"  [4] VALIDASI: rows & hash AFTER == BEFORE")
            if args.rename:
                print(f"  [5] DROP TABLE {db}.\"{tbl}\";")
                print(f"      ALTER TABLE {db}.\"{dst}\" RENAME TO \"{tbl}\";")
            continue

        try:
            existing = client.scalar(
                "SELECT count(*) FROM information_schema.tables "
                f"WHERE table_schema='{db}' AND table_name='{dst}'")
            if int(existing) > 0:
                print(f"  [SKIP] {db}.{dst} sudah ada — tidak ditimpa "
                      f"(hapus/rename manual dulu bila ingin ulang).")
                results.append((f"{db}.{dst}", False, None, None, None, None))
                continue

            n_before, h_before, cols, sql_before = fetch_signature(client, db, tbl)
            print(f"  BEFORE rows={n_before} hash={h_before} cols={len(cols)}")

            client.query(ctas_sql(db, tbl, dst, args.target_base))
            print(f"  CTAS -> {db}.{dst} selesai (location={args.target_base}/{db}.db/{dst})")

            n_after, h_after, _, _ = fetch_signature(client, db, dst)
            print(f"  AFTER  rows={n_after} hash={h_after}")

            ok = (n_before == n_after) and (h_before == h_after)
            print(f"  VALIDASI: {'LULUS' if ok else 'GAGAL'}")
            results.append((f"{db}.{tbl}", ok, n_before, n_after, h_before, h_after))

            if ok and args.rename:
                client.query(f'DROP TABLE {db}."{tbl}"')
                client.query(f'ALTER TABLE {db}."{dst}" RENAME TO "{tbl}"')
                print(f"  RENAME: {dst} -> {tbl} (nama asli dipertahankan)")
            elif not ok:
                print(f"  TIDAK rename (validasi gagal). Salinan {dst} dibiarkan untuk inspeksi.")
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {type(exc).__name__}: {exc}")
            results.append((f"{db}.{tbl}", False, None, None, None, None))

    print("\n" + "=" * 72)
    print("RINGKASAN")
    for name, ok, nb, na, hb, ha in results:
        print(f"  {'LULUS' if ok else 'GAGAL'}  {name}  rows {nb}->{na}  hash {'sama' if hb==ha else 'BEDA'}")
    if args.dry_run:
        print("\n[dry-run] tidak ada perintah yang dieksekusi.")
    return 0 if (args.dry_run or all(r[1] for r in results)) else 1


if __name__ == "__main__":
    sys.exit(main())
