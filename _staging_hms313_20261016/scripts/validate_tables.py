#!/usr/bin/env python3
"""STAGING - Validasi tabel produksi setelah registrasi / migrasi.

Membandingkan kondisi tabel di Trino (membaca via HMS) dengan `manifest_63.json`
yang dibekukan SEBELUM perubahan:
  - SEMUA tabel         : jumlah baris harus sama.
  - kategori s3_minio    : snapshot_id harus sama (bukti register_table TIDAK
                           membuat snapshot baru).
  - kategori file_trino_local: snapshot_id WAJAR berbeda setelah migrasi,
                           sehingga hanya jumlah baris yang diwajibkan sama
                           (kesamaan isi divalidasi oleh migrate_file_tables.py
                           lewat content-hash).

Contoh:
  python validate_tables.py --manifest .../manifest_63.json --trino-url http://localhost:8082
  python validate_tables.py --manifest .../manifest_63.json --dry-run
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _trino_client import TrinoClient  # noqa: E402


def load(manifest_path, only, categories):
    with open(manifest_path, "r", encoding="utf-8-sig") as fh:
        manifest = json.load(fh)
    tables = manifest["tables"] if isinstance(manifest, dict) else manifest
    sel = [t for t in tables if t["category"] in categories]
    if only:
        wanted = set(only)
        sel = [t for t in sel if f"{t['db']}.{t['tbl']}" in wanted]
    return sel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--trino-url", default="http://localhost:8082")
    ap.add_argument("--catalog", default="iceberg")
    ap.add_argument("--tables", default="")
    ap.add_argument("--categories", default="s3_minio,file_trino_local")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    categories = {c.strip() for c in args.categories.split(",") if c.strip()}
    only = [t.strip() for t in args.tables.split(",") if t.strip()]
    tables = load(args.manifest, only, categories)

    print("=" * 72)
    print(f"validate {len(tables)} tabel vs manifest  ({'DRY-RUN' if args.dry_run else 'EXECUTE'})")
    print("=" * 72)

    if args.dry_run:
        for t in tables:
            print(f"SELECT count(*) FROM {args.catalog}.{t['db']}.\"{t['tbl']}\";  -- exp rows={t['rows']}")
            if t["category"] == "s3_minio":
                print(f"SELECT snapshot_id FROM {args.catalog}.{t['db']}.\"{t['tbl']}$snapshots\" "
                      f"ORDER BY committed_at DESC LIMIT 1;  -- exp {t['snapshot_id']}")
        return 0

    client = TrinoClient(url=args.trino_url, catalog=args.catalog, schema="gold")
    bad = []
    for t in tables:
        db, tbl = t["db"], t["tbl"]
        fq = f"{db}.{tbl}"
        try:
            n = int(client.scalar(f'SELECT count(*) FROM {args.catalog}.{db}."{tbl}"'))
            rows_ok = (n == int(t["rows"]))
            snap_ok, snap = True, None
            if t["category"] == "s3_minio":
                snap = client.scalar(
                    f'SELECT snapshot_id FROM {args.catalog}.{db}."{tbl}$snapshots" '
                    "ORDER BY committed_at DESC LIMIT 1")
                snap_ok = (snap is None) or (str(snap) == str(t["snapshot_id"]))
            ok = rows_ok and snap_ok
            mark = "OK  " if ok else "BAD "
            detail = f"rows={n}/{t['rows']}"
            if t["category"] == "s3_minio":
                detail += f" snap={snap}/{t['snapshot_id']}"
            print(f"  [{mark}] {fq:45s} {detail}")
            if not ok:
                bad.append(fq)
        except Exception as exc:  # noqa: BLE001
            print(f"  [ERR ] {fq}: {type(exc).__name__}: {exc}")
            bad.append(fq)

    print("=" * 72)
    if bad:
        print(f"GAGAL: {len(bad)} tabel bermasalah -> {bad}")
        return 1
    print(f"LULUS: semua {len(tables)} tabel cocok dengan manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
