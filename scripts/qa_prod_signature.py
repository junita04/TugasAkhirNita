"""Rekam signature PRODUKSI (READ-ONLY).

Dipakai bersama pipeline QA: jalankan SEKALI sebelum pipeline QA dan SEKALI
sesudah, lalu bandingkan keluarannya. Skrip ini HANYA menjalankan query
baca (SHOW TABLES / SELECT COUNT / SELECT snapshot_id) dan menghitung hash
file model. TIDAK menulis tabel, TIDAK menyentuh artefak.

Contoh:
    python scripts/qa_prod_signature.py --out prod_before.json
    # ... jalankan qa_full_pipeline ...
    python scripts/qa_prod_signature.py --out prod_after.json
    # bandingkan prod_before.json vs prod_after.json

Menjalankan dari host: gunakan --trino-url http://localhost:8082/v1/statement
Menjalankan di container Airflow: --trino-url http://trino:8082/v1/statement
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SCHEMAS = ["bronze", "silver", "gold", "feature_store"]
DEFAULT_MODEL_FILES = [
    "model_a_utama.joblib",
    "model_b_pembanding.joblib",
    "model_a_utama_metadata.json",
    "model_b_pembanding_metadata.json",
]


def trino_query(sql: str, url: str, user: str = "signature", timeout: int = 120):
    """Eksekusi satu SQL read-only via Trino REST API (plain-text body)."""
    req = urllib.request.Request(
        url,
        data=sql.encode("utf-8"),
        headers={
            "X-Trino-User": user,
            "X-Trino-Catalog": "iceberg",
            "Content-Type": "text/plain",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.load(resp)

    rows = []
    deadline_guard = 0
    next_uri = result.get("nextUri")
    while next_uri:
        deadline_guard += 1
        if deadline_guard > 10000:
            raise RuntimeError("Trino polling melebihi batas")
        poll = urllib.request.Request(next_uri, headers={"X-Trino-User": user})
        with urllib.request.urlopen(poll, timeout=timeout) as resp:
            result = json.load(resp)
        if "error" in result:
            raise RuntimeError(
                "Trino error: " + str(result["error"].get("message", result["error"]))[:400]
            )
        if "data" in result:
            rows = result["data"]
        next_uri = result.get("nextUri")
    return rows


def _scalar(sql: str, url: str):
    rows = trino_query(sql, url)
    if not rows or not rows[0]:
        return None
    return rows[0][0]


def table_signatures(schemas, catalog: str, url: str) -> dict:
    signatures = {}
    for schema in schemas:
        try:
            rows = trino_query(f"SHOW TABLES FROM {catalog}.{schema}", url)
        except Exception as exc:  # noqa: BLE001
            signatures[f"{schema}.*"] = {"error": str(exc)[:300]}
            continue

        for row in rows:
            name = row[0]
            entry = {}
            try:
                entry["rows"] = int(_scalar(f"SELECT COUNT(*) FROM {catalog}.{schema}.\"{name}\"", url))
            except Exception as exc:  # noqa: BLE001
                entry["rows_error"] = str(exc)[:200]
            try:
                snap = _scalar(
                    f'SELECT snapshot_id FROM {catalog}.{schema}."{name}$snapshots" '
                    f"ORDER BY committed_at DESC LIMIT 1",
                    url,
                )
                if snap is not None:
                    entry["snapshot_id"] = str(snap)
            except Exception:  # noqa: BLE001
                pass
            signatures[f"{schema}.{name}"] = entry
    return signatures


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_signatures(models_dir: Path, filenames) -> dict:
    result = {}
    if not models_dir.exists():
        return {"_missing_dir": str(models_dir)}
    for name in filenames:
        path = models_dir / name
        if path.is_file():
            result[name] = {
                "sha256": sha256_of(path),
                "bytes": path.stat().st_size,
            }
    # File model lain di level teratas (TIDAK rekursif; subfolder qa dikecualikan).
    for path in sorted(models_dir.glob("*.joblib")):
        if path.name not in result:
            result[path.name] = {"sha256": sha256_of(path), "bytes": path.stat().st_size}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rekam signature produksi (read-only)")
    parser.add_argument(
        "--trino-url",
        default="http://localhost:8082/v1/statement",
        help="Endpoint Trino /v1/statement",
    )
    parser.add_argument("--catalog", default="iceberg")
    parser.add_argument("--schemas", default=",".join(DEFAULT_SCHEMAS))
    parser.add_argument("--models-dir", default=None)
    parser.add_argument("--out", default=None, help="Tulis JSON ke file (default: stdout)")
    parser.add_argument("--skip-trino", action="store_true", help="Hanya hash model")
    args = parser.parse_args(argv)

    proj_root = Path(__file__).resolve().parents[1]
    models_dir = Path(args.models_dir) if args.models_dir else (proj_root / "models")
    schemas = [s.strip() for s in args.schemas.split(",") if s.strip()]

    signature = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "trino_url": args.trino_url,
        "schemas": schemas,
        "tables": {},
        "model_files": model_signatures(models_dir, DEFAULT_MODEL_FILES),
    }

    if not args.skip_trino:
        signature["tables"] = table_signatures(schemas, args.catalog, args.trino_url)

    text = json.dumps(signature, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Signature tersimpan: {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
