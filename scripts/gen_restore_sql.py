"""Generate SQL untuk restore tabel Iceberg ke Hive Metastore via Trino register_table."""
import json
from pathlib import Path

INV = Path(r"D:\TA\TugasAkhirNita\scripts\iceberg_table_inventory.json")
OUT_SQL = Path(r"D:\TA\TugasAkhirNita\scripts\restore_iceberg_tables.sql")
OUT_MANIFEST = Path(r"D:\TA\TugasAkhirNita\scripts\restore_manifest.json")

tables = json.loads(INV.read_text(encoding="utf-8"))

# Tabel yang sudah ter-registrasi (dibuat via Trino langsung)
SKIP = {("gold", "inference_result_model_a_utama")}

schemas = sorted({t["schema"] for t in tables})

WAREHOUSE = "s3://warehouse/iceberg"

lines = []
lines.append("-- Restore Iceberg tables ke Hive Metastore via Trino register_table")
lines.append("")

for s in schemas:
    lines.append(f"CREATE SCHEMA IF NOT EXISTS iceberg.{s};")

lines.append("")

manifest = []
for t in tables:
    schema, table = t["schema"], t["table"]
    if (schema, table) in SKIP:
        continue
    # Path lokasi di MinIO
    if t["preferred_style"] == "hive_db":
        loc = f"{WAREHOUSE}/{schema}.db/{table}"
    else:
        loc = f"{WAREHOUSE}/{schema}/{table}"
    sql = (
        f"CALL iceberg.system.register_table("
        f"schema_name => '{schema}', "
        f"table_name => '{table}', "
        f"table_location => '{loc}')"
    )
    lines.append(sql)
    manifest.append({
        "schema": schema,
        "table": table,
        "location": loc,
        "style": t["preferred_style"],
        "last_modified": t["preferred_last_modified"],
    })

OUT_SQL.write_text("\n".join(lines) + "\n", encoding="utf-8")
OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print(f"Schemas: {schemas}")
print(f"SQL statements: {len(lines)}")
print(f"Tables to register: {len(manifest)}")
print(f"Wrote {OUT_SQL}")
print(f"Wrote {OUT_MANIFEST}")
