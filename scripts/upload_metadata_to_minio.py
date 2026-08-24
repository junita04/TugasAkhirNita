"""
Step 1: Recover original Avro from MinIO to local (overwrite corrupted ones)
Step 2: Delete .crc checksum files (causing errors due to fastavro corruption)
Step 3: Rewrite Avro paths using fastavro (no .crc = no checksum validation)
Step 4: Update metadata JSON (already done, just verify)
Step 5: Upload everything to MinIO
"""
import sys, os, glob, shutil
sys.path.insert(0, '/opt/airflow')
os.environ['SPARK_EVENT_LOG'] = 'false'

from pyspark.sql import SparkSession
import fastavro, io

spark = SparkSession.builder \
    .appName("FixMetadataPaths") \
    .master("local[*]") \
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

jvm = spark.sparkContext._jvm
hadoop = jvm.org.apache.hadoop.fs
uri = jvm.java.net.URI
conf = spark.sparkContext._jsc.hadoopConfiguration()

LOCAL_BASE = "/data/iceberg"
S3A_BASE = "s3a://warehouse/iceberg"

local_path = hadoop.Path(uri("file://" + LOCAL_BASE))
local_fs = local_path.getFileSystem(conf)
s3a_path = hadoop.Path(uri(S3A_BASE))
s3a_fs = s3a_path.getFileSystem(conf)

# Step 1: Recover original Avro files from MinIO
print("Step 1: Recovering Avro files from MinIO...")
recovered = 0
for root, dirs, files in os.walk(LOCAL_BASE):
    for fname in files:
        if fname.endswith('.avro'):
            local_file = os.path.join(root, fname)
            rel = os.path.relpath(local_file, LOCAL_BASE).replace('\\', '/')
            s3a_file_path = f"{S3A_BASE}/{rel}"
            s3a_p = hadoop.Path(uri(s3a_file_path))
            if s3a_fs.exists(s3a_p):
                local_p = hadoop.Path(uri(f"file://{local_file}"))
                jvm.org.apache.hadoop.fs.FileUtil.copy(s3a_fs, s3a_p, local_fs, local_p, True, conf)
                recovered += 1
print(f"  Recovered {recovered} Avro files")

# Step 2: Delete ALL .crc files
print("Step 2: Deleting .crc files...")
crc_count = 0
for root, dirs, files in os.walk(LOCAL_BASE):
    for fname in files:
        if fname.startswith('.crc') or fname.endswith('.crc'):
            os.remove(os.path.join(root, fname))
            crc_count += 1
print(f"  Deleted {crc_count} .crc files")

# Step 3: Rewrite Avro paths
print("Step 3: Rewriting Avro file paths...")
OLD_PREFIXES = ["file:/D:/TA/TugasAkhirNita/iceberg", "file:///D:/TA/TugasAkhirNita/iceberg"]
avro_updated = 0

for root, dirs, files in os.walk(LOCAL_BASE):
    for fname in files:
        if fname.endswith('.avro'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'rb') as f:
                reader = fastavro.reader(f)
                schema = reader.writer_schema
                records = list(reader)
            
            changed = False
            for record in records:
                # Snap list: manifest_path
                if 'manifest_path' in record:
                    mp = record['manifest_path']
                    for old_p in OLD_PREFIXES:
                        if mp.startswith(old_p):
                            record['manifest_path'] = mp.replace(old_p, S3A_BASE, 1)
                            changed = True
                            break
                
                # Manifest: data_file.file_path
                if 'data_file' in record and isinstance(record['data_file'], dict):
                    fp = record['data_file'].get('file_path', '')
                    for old_p in OLD_PREFIXES:
                        if fp.startswith(old_p):
                            record['data_file']['file_path'] = fp.replace(old_p, S3A_BASE, 1)
                            changed = True
                            break
            
            if changed:
                buf = io.BytesIO()
                fastavro.writer(buf, schema, records)
                with open(fpath, 'wb') as f:
                    f.write(buf.getvalue())
                avro_updated += 1

print(f"  Updated {avro_updated} Avro files")

# Step 4: Verify metadata JSON
print("Step 4: Verifying metadata JSON...")
json_ok = 0
json_bad = 0
for root, dirs, files in os.walk(LOCAL_BASE):
    for fname in files:
        if fname.endswith('.metadata.json'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r') as f:
                data = __import__('json').load(f)
            loc = data.get('location', '')
            if loc.startswith('s3a://'):
                json_ok += 1
            else:
                json_bad += 1
print(f"  JSON OK: {json_ok}, JSON bad: {json_bad}")

# Step 5: Upload all to MinIO
print("Step 5: Uploading to MinIO...")
uploaded = 0
for root, dirs, files in os.walk(LOCAL_BASE):
    for fname in files:
        if fname.endswith('.json') or fname.endswith('.avro') or fname == 'version-hint.text':
            local_file = os.path.join(root, fname)
            rel = os.path.relpath(local_file, LOCAL_BASE).replace('\\', '/')
            dest = hadoop.Path(uri(f"{S3A_BASE}/{rel}"))
            parent = dest.getParent()
            if not s3a_fs.exists(parent):
                s3a_fs.mkdirs(parent)
            local_p = hadoop.Path(uri(f"file://{local_file}"))
            local_fs_for_copy = local_p.getFileSystem(conf)
            jvm.org.apache.hadoop.fs.FileUtil.copy(local_fs_for_copy, local_p, s3a_fs, dest, True, conf)
            uploaded += 1

print(f"  Uploaded {uploaded} files to MinIO")

# Final verification
print("Step 6: Final verification...")
for table_path in ["bronze/data_referensi_mahasiswa", "silver/silver_mahasiswa", "gold/dim_mahasiswa"]:
    meta_dir = hadoop.Path(uri(f"{S3A_BASE}/{table_path}/metadata"))
    if s3a_fs.exists(meta_dir):
        statuses = s3a_fs.listStatus(meta_dir)
        json_files = [s for s in statuses if s.getPath().getName().endswith('.json')]
        avro_files = [s for s in statuses if s.getPath().getName().endswith('.avro')]
        print(f"  {table_path}: {len(json_files)} JSON, {len(avro_files)} Avro")

spark.stop()
print("ALL_DONE")
