"""
Update all Iceberg metadata paths from file:///D:/TA/TugasAkhirNita/iceberg/...
to s3a://warehouse/iceberg/...

Updates 3 layers:
1. v*.metadata.json -> location field
2. snap-*.avro -> manifest_path field
3. *-m*.avro -> data_file.file_path field
"""
import json
import glob
import os
import fastavro
import io

OLD_PREFIX = 'file:///D:/TA/TugasAkhirNita/iceberg'
OLD_PREFIX_SLASH = 'file:/D:/TA/TugasAkhirNita/iceberg'
NEW_PREFIX = 's3a://warehouse/iceberg'

BASE = 'D:/TA/TugasAkhirNita/iceberg'

def update_metadata_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    loc = data.get('location', '')
    changed = False
    if loc.startswith(OLD_PREFIX):
        data['location'] = loc.replace(OLD_PREFIX, NEW_PREFIX, 1)
        changed = True
    elif loc.startswith(OLD_PREFIX_SLASH):
        data['location'] = loc.replace(OLD_PREFIX_SLASH, NEW_PREFIX, 1)
        changed = True
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    return changed

def update_avro_paths(filepath):
    with open(filepath, 'rb') as f:
        reader = fastavro.reader(f)
        schema = reader.writer_schema
        records = list(reader)
    
    changed = False
    for record in records:
        # Snap list: manifest_path
        if 'manifest_path' in record:
            mp = record['manifest_path']
            if mp.startswith(OLD_PREFIX_SLASH):
                record['manifest_path'] = mp.replace(OLD_PREFIX_SLASH, NEW_PREFIX, 1)
                changed = True
            elif mp.startswith(OLD_PREFIX):
                record['manifest_path'] = mp.replace(OLD_PREFIX, NEW_PREFIX, 1)
                changed = True
        
        # Manifest: data_file.file_path
        if 'data_file' in record and isinstance(record['data_file'], dict):
            fp = record['data_file'].get('file_path', '')
            if fp.startswith(OLD_PREFIX_SLASH):
                record['data_file']['file_path'] = fp.replace(OLD_PREFIX_SLASH, NEW_PREFIX, 1)
                changed = True
            elif fp.startswith(OLD_PREFIX):
                record['data_file']['file_path'] = fp.replace(OLD_PREFIX, NEW_PREFIX, 1)
                changed = True
    
    if changed:
        buf = io.BytesIO()
        fastavro.writer(buf, schema, records)
        with open(filepath, 'wb') as f:
            f.write(buf.getvalue())
    
    return changed

# Count stats
meta_changed = 0
meta_total = 0
snap_changed = 0
snap_total = 0
manifest_changed = 0
manifest_total = 0

# 1. Update metadata JSON
for fp in glob.glob(os.path.join(BASE, '**', '**', 'metadata', 'v*.metadata.json'), recursive=True):
    meta_total += 1
    if update_metadata_json(fp):
        meta_changed += 1

# 2. Update snap list (manifest list)
for fp in glob.glob(os.path.join(BASE, '**', '**', 'metadata', 'snap-*.avro'), recursive=True):
    snap_total += 1
    if update_avro_paths(fp):
        snap_changed += 1

# 3. Update manifest files
for fp in glob.glob(os.path.join(BASE, '**', '**', 'metadata', '*-m*.avro'), recursive=True):
    manifest_total += 1
    if update_avro_paths(fp):
        manifest_changed += 1

print(f'metadata.json: {meta_changed}/{meta_total} updated')
print(f'snap-*.avro:   {snap_changed}/{snap_total} updated')
print(f'*-m*.avro:     {manifest_changed}/{manifest_total} updated')
print(f'TOTAL:         {meta_changed + snap_changed + manifest_changed} files updated')
