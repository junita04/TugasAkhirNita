"""Restore semua tabel Iceberg lama dari MinIO ke Hive Metastore via Trino.

Langkah:
  1. CREATE SCHEMA IF NOT EXISTS untuk bronze/silver/gold/feature_store
  2. SHOW TABLES per schema -> daftar yang sudah terdaftar (skip)
  3. CALL iceberg.system.register_table untuk setiap tabel manifest yang belum ada
  4. SELECT count(*) per tabel untuk verifikasi
  5. Tulis laporan JSON

Pakai Trino REST API plain-text body (validasi sesi ini), dari host
via port published 8082.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

TRINO_URL = "http://localhost:8082/v1/statement"
BASE_HEADERS = {
    "X-Trino-User": "restore",
    "X-Trino-Catalog": "iceberg",
    "X-Trino-Schema": "default",
}
TIMEOUT = 120

MANIFEST = Path(r"D:\TA\TugasAkhirNita\scripts\restore_manifest.json")
REPORT = Path(r"D:\TA\TugasAkhirNita\scripts\restore_report.json")

SCHEMAS = ["bronze", "silver", "gold", "feature_store"]


class TrinoError(RuntimeError):
    pass


def _post(req_url, headers, data=None):
    req = urllib.request.Request(req_url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            j = json.loads(body)
            if "error" in j:
                raise TrinoError(j["error"].get("message", str(j["error"])))
        except json.JSONDecodeError:
            pass
        raise TrinoError(f"HTTP {e.code}: {body[:300]}")


def trino_execute(sql):
    """Eksekusi SQL, poll sampai selesai. Return list-of-lists rows."""
    result = _post(TRINO_URL, dict(BASE_HEADERS), data=sql.encode("utf-8"))
    if "error" in result:
        raise TrinoError(result["error"].get("message", str(result["error"])))

    rows = []
    next_uri = result.get("nextUri")
    while next_uri:
        poll_headers = {"X-Trino-User": BASE_HEADERS["X-Trino-User"]}
        req = urllib.request.Request(next_uri, headers=poll_headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise TrinoError(f"poll HTTP {e.code}: {body[:300]}")
        if "error" in result:
            raise TrinoError(result["error"].get("message", str(result["error"])))
        if "data" in result:
            rows = result["data"]
        next_uri = result.get("nextUri")
    return rows


def qident(name):
    return '"' + name.replace('"', '""') + '"'


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = {"schemas_created": [], "skipped_existing": [], "registered": [],
              "register_failed": [], "verified": [], "verify_failed": []}

    # 1. Schemas
    for s in SCHEMAS:
        try:
            trino_execute(f"CREATE SCHEMA IF NOT EXISTS iceberg.{qident(s)}")
            report["schemas_created"].append(s)
            print(f"[schema] OK   {s}")
        except TrinoError as e:
            print(f"[schema] FAIL {s}: {e}")

    # 2. Existing tables per schema
    existing = set()
    for s in SCHEMAS:
        try:
            rows = trino_execute(f"SHOW TABLES IN iceberg.{qident(s)}")
            for r in rows:
                existing.add((s, r[0]))
            print(f"[show]   {s}: {len(rows)} tabel terdaftar")
        except TrinoError as e:
            print(f"[show]   {s}: GAGAL ({e})")

    # 3. Register
    for entry in manifest:
        schema, table, loc = entry["schema"], entry["table"], entry["location"]
        if (schema, table) in existing:
            report["skipped_existing"].append(f"{schema}.{table}")
            continue
        sql = (
            "CALL iceberg.system.register_table("
            f"schema_name => '{schema}', "
            f"table_name => '{table}', "
            f"table_location => '{loc}')"
        )
        try:
            trino_execute(sql)
            report["registered"].append(f"{schema}.{table}")
            print(f"[reg]    OK   {schema}.{table}")
        except TrinoError as e:
            report["register_failed"].append({"table": f"{schema}.{table}", "error": str(e)[:500]})
            print(f"[reg]    FAIL {schema}.{table}: {str(e)[:200]}")

    # 4. Verify counts untuk semua tabel di manifest (termasuk yang skip)
    for entry in manifest:
        schema, table = entry["schema"], entry["table"]
        ident = f"{qident(schema)}.{qident(table)}"
        try:
            rows = trino_execute(f"SELECT count(*) FROM {ident}")
            cnt = rows[0][0] if rows else "?"
            report["verified"].append({"table": f"{schema}.{table}", "rows": int(cnt) if str(cnt).lstrip("-").isdigit() else cnt})
            print(f"[count]  {schema}.{table} = {cnt}")
        except TrinoError as e:
            report["verify_failed"].append({"table": f"{schema}.{table}", "error": str(e)[:500]})
            print(f"[count]  FAIL {schema}.{table}: {str(e)[:200]}")

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"Skipped (sudah ada) : {len(report['skipped_existing'])}")
    print(f"Registered baru     : {len(report['registered'])}")
    print(f"Register gagal      : {len(report['register_failed'])}")
    print(f"Verified OK         : {len(report['verified'])}")
    print(f"Verify gagal        : {len(report['verify_failed'])}")
    print(f"Laporan: {REPORT}")

    if report["register_failed"] or report["verify_failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
