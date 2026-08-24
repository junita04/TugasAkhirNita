import fastavro
import glob
import os

# Check data_file structure inside manifest
manifests = glob.glob('D:/TA/TugasAkhirNita/iceberg/bronze/data_referensi_mahasiswa/metadata/*-m0.avro')
if manifests:
    manifests.sort()
    latest = manifests[-1]
    print(f'Reading manifest: {os.path.basename(latest)}')
    with open(latest, 'rb') as f:
        reader = fastavro.reader(f)
        for i, record in enumerate(reader):
            df = record.get('data_file', {})
            fp = df.get('file_path', 'N/A') if isinstance(df, dict) else 'data_file not dict'
            print(f'  file_path: {fp}')
            if i >= 2:
                break
