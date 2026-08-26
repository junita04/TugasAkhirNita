import fastavro
import json
import os
import io

WORK_DIR = "D:/TA/TugasAkhirNita/temp_metadata/silver_work"
OLD_PREFIXES = ["file:/D:/TA/TugasAkhirNita/iceberg", "file:///D:/TA/TugasAkhirNita/iceberg"]
NEW_PREFIX = "s3a://warehouse/iceberg"

print("=" * 60)
print("REWRITE AVRO PATHS: file:/// -> s3a://")
print("=" * 60)

# 1. Rewrite snap-*.avro (manifest list)
snap_file = os.path.join(WORK_DIR, "snap-5908813751930038862-1-4428f920-f2bb-43a6-87be-affaa7a84671.avro")
with open(snap_file, "rb") as f:
    reader = fastavro.reader(f)
    schema = reader.writer_schema
    records = list(reader)

for record in records:
    mp = record.get("manifest_path", "")
    for old_p in OLD_PREFIXES:
        if mp.startswith(old_p):
            record["manifest_path"] = mp.replace(old_p, NEW_PREFIX, 1)
            print(f"  snap avro manifest_path: {mp} -> {record['manifest_path']}")
            break

buf = io.BytesIO()
fastavro.writer(buf, schema, records)
with open(snap_file, "wb") as f:
    f.write(buf.getvalue())
print(f"  [UPDATED] snap avro")

# 2. Rewrite manifest-*.avro (manifest with data files)
manifest_file = os.path.join(WORK_DIR, "4428f920-f2bb-43a6-87be-affaa7a84671-m0.avro")
with open(manifest_file, "rb") as f:
    reader = fastavro.reader(f)
    schema = reader.writer_schema
    records = list(reader)

count = 0
for record in records:
    df = record.get("data_file", {})
    if isinstance(df, dict):
        fp = df.get("file_path", "")
        for old_p in OLD_PREFIXES:
            if fp.startswith(old_p):
                df["file_path"] = fp.replace(old_p, NEW_PREFIX, 1)
                print(f"  manifest file_path: {fp} -> {df['file_path']}")
                count += 1
                break

buf = io.BytesIO()
fastavro.writer(buf, schema, records)
with open(manifest_file, "wb") as f:
    f.write(buf.getvalue())
print(f"  [UPDATED] manifest avro ({count} data files)")

# 3. Rewrite v1.metadata.json
v1_file = os.path.join(WORK_DIR, "v1.metadata.json")
with open(v1_file, "r", encoding="utf-8") as f:
    data = json.load(f)

changed = False
loc = data.get("location", "")
for old_p in OLD_PREFIXES:
    if loc.startswith(old_p):
        data["location"] = loc.replace(old_p, NEW_PREFIX, 1)
        print(f"  v1 location: {loc} -> {data['location']}")
        changed = True
        break

for snap in data.get("snapshots", []):
    ml = snap.get("manifest-list", "")
    for old_p in OLD_PREFIXES:
        if ml.startswith(old_p):
            snap["manifest-list"] = ml.replace(old_p, NEW_PREFIX, 1)
            print(f"  v1 manifest-list: {ml} -> {snap['manifest-list']}")
            changed = True
            break

if changed:
    with open(v1_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  [UPDATED] v1.metadata.json")

# 4. Rewrite 00000-*.metadata.json
meta0_file = os.path.join(WORK_DIR, "00000-ba0f8dea-cd1f-4cb4-9381-e36f9cba79cf.metadata.json")
with open(meta0_file, "r", encoding="utf-8") as f:
    data = json.load(f)

loc = data.get("location", "")
for old_p in OLD_PREFIXES:
    if loc.startswith(old_p):
        data["location"] = loc.replace(old_p, NEW_PREFIX, 1)
        print(f"  00000 location: {loc} -> {data['location']}")
        break
# Also check for s3:// -> s3a://
if data.get("location", "").startswith("s3://"):
    data["location"] = data["location"].replace("s3://", "s3a://", 1)
    print(f"  00000 location s3->s3a: {data['location']}")

with open(meta0_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print(f"  [UPDATED] 00000 metadata.json")

print()
print("=" * 60)
print("REWRITE COMPLETE")
print("=" * 60)
