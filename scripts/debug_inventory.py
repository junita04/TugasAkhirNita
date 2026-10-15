import json
import re
from pathlib import Path

INV = Path(r"D:\TA\TugasAkhirNita\scripts\minio_inventory.jsonl")

lines = [l for l in INV.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
print("total lines:", len(lines))

ok = 0
fail = 0
sample_keys = []
for line in lines[:5]:
    try:
        obj = json.loads(line)
        sample_keys.append(obj.get("key", ""))
    except Exception as e:
        print("json err:", e)
print("sample keys:", sample_keys)

pat_hive = re.compile(r"^(?P<schema>[^/]+)\.db/(?P<table>[^/]+)/metadata/[^/]+\.metadata\.json$")
n_match = 0
n_meta = 0
for line in lines:
    try:
        obj = json.loads(line)
    except Exception:
        fail += 1
        continue
    ok += 1
    key = obj.get("key", "")
    if key.endswith(".metadata.json"):
        n_meta += 1
        if pat_hive.match(key):
            n_match += 1
print("parsed ok:", ok, "fail:", fail)
print("metadata keys:", n_meta, "hive matched:", n_match)
