import boto3
import json

s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin-password",
)

# Check metadata files for _fix tables
for schema, table in [("gold", "dim_mahasiswa_fix"), ("gold", "fact_khs_fix")]:
    prefix = f"iceberg/{schema}/{table}/metadata/"
    print(f"\n=== {schema}.{table} ===")
    
    resp = s3.list_objects_v2(Bucket="warehouse", Prefix=prefix)
    for obj in resp.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".json"):
            print(f"  {key} ({obj['Size']} bytes)")
            # Read the metadata file
            resp2 = s3.get_object(Bucket="warehouse", Key=key)
            content = resp2["Body"].read().decode("utf-8")
            meta = json.loads(content)
            print(f"    format-version: {meta.get('format-version')}")
            print(f"    table-uuid: {meta.get('table-uuid', 'N/A')[:20]}...")
            if "current-snapshot-id" in meta:
                print(f"    current-snapshot-id: {meta['current-snapshot-id']}")
            if "snapshots" in meta:
                print(f"    snapshots: {len(meta['snapshots'])}")
