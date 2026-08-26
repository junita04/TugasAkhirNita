import fastavro
import io, sys

with open('/tmp/snap.avro', 'rb') as f:
    reader = fastavro.reader(f)
    for record in reader:
        if 'manifest_path' in record:
            print("manifest_path:", record['manifest_path'])
        elif isinstance(record, dict):
            for k, v in record.items():
                if 'path' in k.lower() or 'manifest' in k.lower() or 'file' in k.lower():
                    print(f"{k}: {v}")
            if 'entries' in record:
                for entry in record['entries'][:3]:
                    print("entry:", {k: v for k, v in entry.items() if 'path' in k.lower() or 'file' in k.lower()})
