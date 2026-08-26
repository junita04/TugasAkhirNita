import fastavro, sys

filepath = sys.argv[1]
with open(filepath, 'rb') as f:
    reader = fastavro.reader(f)
    for i, record in enumerate(reader):
        print(f"Record {i}:")
        for k, v in record.items():
            val = str(v)
            if len(val) > 200:
                val = val[:200] + "..."
            print(f"  {k}: {val}")
        if i > 2:
            break
