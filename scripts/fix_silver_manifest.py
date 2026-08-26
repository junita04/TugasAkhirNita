"""
Fix Iceberg manifest paths for silver.data_referensi_mahasiswa.

Reads Avro files from MinIO (S3A), rewrites file:/// paths to s3a:// paths,
and uploads back. Does NOT touch Parquet data files.

Usage: Run from Airflow container (has fastavro + Spark JARs).
"""
import sys
import os
import json
import shutil
import tempfile
import fastavro
import io

# S3A config
S3A_BASE = "s3a://warehouse/iceberg"
TABLE_PATH = "silver/data_referensi_mahasiswa"
TABLE_METADATA_DIR = f"{S3A_BASE}/{TABLE_PATH}/metadata"

OLD_PREFIXES = [
    "file:/D:/TA/TugasAkhirNita/iceberg",
    "file:///D:/TA/TugasAkhirNita/iceberg",
]

NEW_PREFIX = "s3a://warehouse/iceberg"

# ================================================================
# Step 1: Initialize Spark for S3A access
# ================================================================
print("=" * 60)
print("STEP 1: Initialize Spark session for S3A access")
print("=" * 60)

sys.path.insert(0, "/opt/airflow")
os.environ["SPARK_EVENT_LOG"] = "false"

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("FixSilverManifest")
    .master("local[*]")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.driver.memory", "512m")
    .getOrCreate()
)

jvm = spark.sparkContext._jvm
hadoop = jvm.org.apache.hadoop.fs
uri = jvm.java.net.URI
conf = spark.sparkContext._jsc.hadoopConfiguration()

s3a_path = hadoop.Path(uri(S3A_BASE))
s3a_fs = s3a_path.getFileSystem(conf)

print("  Spark session ready")
print(f"  S3A base: {S3A_BASE}")
print(f"  Table: {TABLE_PATH}")

# ================================================================
# Step 2: Download Avro files from MinIO to temp directory
# ================================================================
print()
print("=" * 60)
print("STEP 2: Download Avro + metadata files from MinIO")
print("=" * 60)

tmpdir = tempfile.mkdtemp(prefix="iceberg_fix_")
print(f"  Temp dir: {tmpdir}")

downloaded_files = []
meta_dir = hadoop.Path(uri(TABLE_METADATA_DIR))
if s3a_fs.exists(meta_dir):
    statuses = s3a_fs.listStatus(meta_dir)
    for status in statuses:
        fname = status.getPath().getName()
        # Only download Avro, JSON metadata, and version-hint
        if (fname.endswith(".avro") or fname.endswith(".metadata.json") 
            or fname == "version-hint.text"):
            s3a_file = status.getPath()
            local_file = os.path.join(tmpdir, fname)
            local_p = hadoop.Path(uri("file://" + local_file))
            local_fs = local_p.getFileSystem(conf)
            hadoop.FileUtil.copy(s3a_fs, s3a_file, local_fs, local_p, True, conf)
            downloaded_files.append(fname)
            print(f"  Downloaded: {fname} ({status.getLen()} bytes)")

print(f"  Total downloaded: {len(downloaded_files)} files")

# ================================================================
# Step 3: Rewrite paths in Avro files using fastavro
# ================================================================
print()
print("=" * 60)
print("STEP 3: Rewrite file:/// paths to s3a:// in Avro files")
print("=" * 60)

avro_updated = 0
avro_files = [f for f in downloaded_files if f.endswith(".avro")]

for fname in avro_files:
    fpath = os.path.join(tmpdir, fname)
    with open(fpath, "rb") as f:
        reader = fastavro.reader(f)
        schema = reader.writer_schema
        records = list(reader)

    changed = False
    for record in records:
        # Snap list: manifest_path
        if "manifest_path" in record:
            mp = record["manifest_path"]
            for old_p in OLD_PREFIXES:
                if mp.startswith(old_p):
                    record["manifest_path"] = mp.replace(old_p, NEW_PREFIX, 1)
                    changed = True
                    print(f"  [{fname}] manifest_path: {mp} -> {record['manifest_path']}")
                    break

        # Manifest: data_file.file_path
        if "data_file" in record and isinstance(record["data_file"], dict):
            fp = record["data_file"].get("file_path", "")
            for old_p in OLD_PREFIXES:
                if fp.startswith(old_p):
                    record["data_file"]["file_path"] = fp.replace(old_p, NEW_PREFIX, 1)
                    changed = True
                    print(f"  [{fname}] file_path: {fp} -> {record['data_file']['file_path']}")
                    break

    if changed:
        buf = io.BytesIO()
        fastavro.writer(buf, schema, records)
        with open(fpath, "wb") as f:
            f.write(buf.getvalue())
        avro_updated += 1
        print(f"  [UPDATED] {fname}")
    else:
        print(f"  [NO CHANGE] {fname}")

print(f"  Avro files updated: {avro_updated}/{len(avro_files)}")

# ================================================================
# Step 4: Update metadata JSON files
# ================================================================
print()
print("=" * 60)
print("STEP 4: Update metadata JSON location fields")
print("=" * 60)

json_updated = 0
json_files = [f for f in downloaded_files if f.endswith(".metadata.json")]

for fname in json_files:
    fpath = os.path.join(tmpdir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    loc = data.get("location", "")
    for old_p in OLD_PREFIXES:
        if loc.startswith(old_p):
            data["location"] = loc.replace(old_p, NEW_PREFIX, 1)
            changed = True
            print(f"  [{fname}] location: {loc} -> {data['location']}")
            break

    # Also fix manifest-list in snapshots
    for snap in data.get("snapshots", []):
        ml = snap.get("manifest-list", "")
        for old_p in OLD_PREFIXES:
            if ml.startswith(old_p):
                snap["manifest-list"] = ml.replace(old_p, NEW_PREFIX, 1)
                changed = True
                print(f"  [{fname}] manifest-list: {ml} -> {snap['manifest-list']}")
                break

    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        json_updated += 1
        print(f"  [UPDATED] {fname}")
    else:
        print(f"  [NO CHANGE] {fname}")

print(f"  JSON files updated: {json_updated}/{len(json_files)}")

# ================================================================
# Step 5: Upload fixed files back to MinIO
# ================================================================
print()
print("=" * 60)
print("STEP 5: Upload fixed files back to MinIO")
print("=" * 60)

uploaded = 0
for fname in os.listdir(tmpdir):
    local_file = os.path.join(tmpdir, fname)
    s3a_file_path = f"{TABLE_METADATA_DIR}/{fname}"
    dest = hadoop.Path(uri(s3a_file_path))
    parent = dest.getParent()
    if not s3a_fs.exists(parent):
        s3a_fs.mkdirs(parent)
    local_p = hadoop.Path(uri("file://" + local_file))
    local_fs_for_copy = local_p.getFileSystem(conf)
    hadoop.FileUtil.copy(local_fs_for_copy, local_p, s3a_fs, dest, True, conf)
    uploaded += 1
    print(f"  Uploaded: {fname}")

print(f"  Total uploaded: {uploaded} files")

# ================================================================
# Step 6: Cleanup temp directory
# ================================================================
print()
print("=" * 60)
print("STEP 6: Cleanup")
print("=" * 60)
shutil.rmtree(tmpdir)
print(f"  Removed temp dir: {tmpdir}")

# ================================================================
# Step 7: Final verification
# ================================================================
print()
print("=" * 60)
print("STEP 7: Final verification on MinIO")
print("=" * 60)

# Read the uploaded v1.metadata.json and verify
v1_path = hadoop.Path(uri(f"{TABLE_METADATA_DIR}/v1.metadata.json"))
if s3a_fs.exists(v1_path):
    # Read via Hadoop FS
    import tempfile as tf
    verify_tmp = os.path.join(tf.gettempdir(), "verify_v1.json")
    verify_p = hadoop.Path(uri("file://" + verify_tmp))
    verify_fs = verify_p.getFileSystem(conf)
    hadoop.FileUtil.copy(s3a_fs, v1_path, verify_fs, verify_p, True, conf)
    
    with open(verify_tmp, "r") as f:
        data = json.load(f)
    print(f"  v1.metadata.json location: {data.get('location')}")
    for s in data.get("snapshots", []):
        print(f"  v1.metadata.json manifest-list: {s.get('manifest-list')}")
    os.remove(verify_tmp)

# Verify Avro files
for avro_name in ["snap-5908813751930038862-1-4428f920-f2bb-43a6-87be-affaa7a84671.avro",
                   "4428f920-f2bb-43a6-87be-affaa7a84671-m0.avro"]:
    avro_path = hadoop.Path(uri(f"{TABLE_METADATA_DIR}/{avro_name}"))
    if s3a_fs.exists(avro_path):
        verify_tmp2 = os.path.join(tf.gettempdir(), f"verify_{avro_name}")
        verify_p2 = hadoop.Path(uri("file://" + verify_tmp2))
        verify_fs2 = verify_p2.getFileSystem(conf)
        hadoop.FileUtil.copy(s3a_fs, avro_path, verify_fs2, verify_p2, True, conf)
        
        with open(verify_tmp2, "rb") as f:
            reader = fastavro.reader(f)
            for i, record in enumerate(reader):
                if "manifest_path" in record:
                    print(f"  {avro_name} manifest_path: {record['manifest_path']}")
                if "data_file" in record and isinstance(record["data_file"], dict):
                    print(f"  {avro_name} file_path: {record['data_file'].get('file_path')}")
                if i >= 1:
                    break
        os.remove(verify_tmp2)

# ================================================================
# Done
# ================================================================
spark.stop()
print()
print("=" * 60)
print("FIX_SILVER_MANIFEST_DONE")
print("=" * 60)
