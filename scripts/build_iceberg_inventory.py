"""Inventarisasi tabel Iceberg di MinIO: deteksi lokasi per (schema, table)."""
import json
import re
from collections import defaultdict
from pathlib import Path

INV = Path(r"D:\TA\TugasAkhirNita\scripts\minio_inventory.jsonl")
OUT = Path(r"D:\TA\TugasAkhirNita\scripts\iceberg_table_inventory.json")

# key: (schema, table) -> {location_style: {last_modified, count_metadata}}
tables = defaultdict(lambda: defaultdict(lambda: {"last_modified": "", "n_meta": 0}))

pat_hive = re.compile(r"^(?P<schema>[^/]+)\.db/(?P<table>[^/]+)/metadata/[^/]+\.metadata\.json$")
pat_spark = re.compile(r"^(?P<schema>bronze|silver|gold|feature_store|default)/(?P<table>[^/]+)/metadata/[^/]+\.metadata\.json$")

for line in INV.read_text(encoding="utf-16", errors="replace").splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        continue
    key = obj.get("key", "")
    lm = obj.get("lastModified", "")
    m = pat_hive.match(key)
    style = "hive_db"
    if not m:
        m = pat_spark.match(key)
        style = "spark"
    if not m:
        continue
    schema, table = m.group("schema"), m.group("table")
    e = tables[(schema, table)][style]
    e["n_meta"] += 1
    if lm > e["last_modified"]:
        e["last_modified"] = lm

# Build result: pick preferred location (most recent last_modified)
result = []
for (schema, table), styles in sorted(tables.items()):
    locs = {s: v for s, v in styles.items()}
    preferred = max(locs.items(), key=lambda kv: (kv[1]["last_modified"], kv[1]["n_meta"]))
    result.append({
        "schema": schema,
        "table": table,
        "preferred_style": preferred[0],
        "preferred_last_modified": preferred[1]["last_modified"],
        "locations": {s: dict(v) for s, v in locs.items()},
    })

OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

print(f"Total unique (schema, table): {len(result)}")
print()
by_schema = defaultdict(list)
for r in result:
    by_schema[r["schema"]].append(r)
for schema in sorted(by_schema):
    print(f"== {schema} ({len(by_schema[schema])} tables)")
    for r in by_schema[schema]:
        both = set(r["locations"].keys())
        note = "BOTH" if len(both) == 2 else ("hive_db" if "hive_db" in both else "spark")
        print(f"   {r['table']:<45} pref={r['preferred_style']:<8} {note:<8} last={r['preferred_last_modified']}")
