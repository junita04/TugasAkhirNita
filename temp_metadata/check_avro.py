import fastavro

# Check snap avro (manifest list)
print("=== snap-*.avro (MANIFEST LIST) ===")
with open("D:/TA/TugasAkhirNita/temp_metadata/silver_backup/snap-5908813751930038862-1-4428f920-f2bb-43a6-87be-affaa7a84671.avro", "rb") as f:
    reader = fastavro.reader(f)
    for i, record in enumerate(reader):
        mp = record.get("manifest_path", "N/A")
        ml = record.get("manifest_length", "N/A")
        afc = record.get("added_files_count", "N/A")
        arc = record.get("added_rows_count", "N/A")
        print("  manifest_path:", mp)
        print("  manifest_length:", ml)
        print("  added_files_count:", afc)
        print("  added_rows_count:", arc)
        print()

# Check manifest avro
print("=== 4428f920-*.avro (MANIFEST) ===")
with open("D:/TA/TugasAkhirNita/temp_metadata/silver_backup/4428f920-f2bb-43a6-87be-affaa7a84671-m0.avro", "rb") as f:
    reader = fastavro.reader(f)
    for i, record in enumerate(reader):
        df = record.get("data_file", {})
        if isinstance(df, dict):
            fp = df.get("file_path", "N/A")
            fs = df.get("file_size_in_bytes", "N/A")
            rc = df.get("record_count", "N/A")
            print("  file_path:", fp)
            print("  file_size:", fs)
            print("  record_count:", rc)
        else:
            mp = record.get("manifest_path", "N/A")
            print("  manifest_path:", mp)
        if i >= 6:
            break
