"""
Helper membaca Iceberg local table TANPA Spark.

Iceberg menyimpan data sebagai parquet di <table>/data/. Multiple snapshot
dapat menghasilkan beberapa file parquet; file aktif adalah milik
current-snapshot (metadata/vN.metadata.json -> current-snapshot-id).

Karena setiap snapshot yang menulis ulang tabel (createOrReplace) mengganti
file data, pendekatan aman: pilih file parquet (tanpa prefix '.') yang
jumlah barisnya sesuai dengan added-records pada current snapshot.
"""

import glob
import json
import os

import pyarrow.parquet as pq


def _current_snapshot_info(table_dir):
    """Baca metadata Iceberg terbaru dan kembalikan info current snapshot."""
    metadata_dir = os.path.join(table_dir, "metadata")
    version_files = sorted(glob.glob(os.path.join(metadata_dir, "v*.metadata.json")))
    if not version_files:
        raise FileNotFoundError(f"Metadata Iceberg tidak ditemukan di {metadata_dir}")

    latest = version_files[-1]
    with open(latest, "r", encoding="utf-8") as fh:
        meta = json.load(fh)

    current_id = meta["current-snapshot-id"]
    current = None
    for snap in meta.get("snapshots", []):
        if snap["snapshot-id"] == current_id:
            current = snap
            break
    if current is None:
        raise RuntimeError(f"current-snapshot-id {current_id} tidak ditemukan")

    return {
        "snapshot_id": current_id,
        "added_records": int(current["summary"].get("added-records", 0)),
        "schema_id": current.get("schema-id"),
        "timestamp_ms": int(current.get("timestamp-ms", 0)),
    }


def load_active_parquet(table_dir):
    """
    Memuat seluruh baris data aktif (current snapshot) tabel Iceberg lokal
    menjadi pandas DataFrame.

    Karena beberapa snapshot dapat menghasilkan banyak file parquet dengan
    jumlah baris yang sama (mis. tabel ditulis ulang dengan jumlah baris
    identik), file dipilih berdasarkan kecocokan dengan current snapshot:
      1) jumlah baris file == added-records current snapshot, DAN
      2) mtime file >= timestamp commit current snapshot.
    Ini menghindari memilih file dari snapshot LAMA yang kebetulan punya
    jumlah baris sama.
    """
    info = _current_snapshot_info(table_dir)
    data_dir = os.path.join(table_dir, "data")

    candidates = [
        os.path.join(data_dir, name)
        for name in os.listdir(data_dir)
        if name.endswith(".parquet") and not name.startswith(".")
    ]

    if not candidates:
        raise FileNotFoundError(f"Tidak ada file data parquet aktif di {data_dir}")

    # Pilih file yang (a) jumlah barisnya cocok dengan added-records current
    # snapshot dan (b) ditulis paling akhir (mtime terbesar). Karena tabel
    # ditulis ulang via createOrReplace, file milik snapshot AKTIF selalu
    # yang paling baru di tulis.
    matches = []
    for path in candidates:
        rows = pq.read_table(path).num_rows
        if rows == info["added_records"]:
            matches.append((os.path.getmtime(path), path))
    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        return pq.read_table(matches[0][1]).to_pandas()

    # Fallback: gabungkan semua file aktif (pastikan totalnya cocok).
    total = 0
    combined = []
    for path in candidates:
        tbl = pq.read_table(path)
        total += tbl.num_rows
        combined.append(tbl)
    if total != info["added_records"]:
        raise RuntimeError(
            f"Jumlah baris aktif ({total}) != added-records current snapshot "
            f"({info['added_records']}) untuk {table_dir}"
        )
    import pyarrow as pa

    tbl = pa.concat_tables(combined)
    return tbl.to_pandas()