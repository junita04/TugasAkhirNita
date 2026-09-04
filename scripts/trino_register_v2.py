import requests
import time

def run_trino(sql):
    r = requests.post('http://trino:8082/v1/statement', 
                      headers={'X-Trino-User': 'admin', 'Content-Type': 'text/plain'}, 
                      data=sql)
    result = r.json()
    all_data = []
    
    for i in range(20):
        data = result.get('data')
        if data:
            all_data.extend(data)
        
        uri = result.get('nextUri')
        if not uri:
            break
        time.sleep(2)
        r = requests.get(uri, headers={'X-Trino-User': 'admin'})
        result = r.json()
    
    return all_data

# Try to register using CALL system.register_table
# First, let's check what metadata location Trino expects

# The issue: Spark created tables via HadoopFileIO, but Trino expects Hive Metastore registered tables
# Let's try to register via Trino's register_table procedure with the correct path

# Check what the metadata location should be
print('=== Trying to register dim_mahasiswa_fix via Trino ===')

# First, check if the table exists in the Iceberg metadata
import boto3
s3 = boto3.client('s3', endpoint_url='http://minio:9000', 
                  aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin-password')

# List metadata files
for schema, table in [('gold', 'dim_mahasiswa_fix'), ('gold', 'fact_khs_fix')]:
    prefix = f'iceberg/{schema}/{table}/metadata/'
    resp = s3.list_objects_v2(Bucket='warehouse', Prefix=prefix)
    files = [obj['Key'] for obj in resp.get('Contents', []) if obj['Key'].endswith('.json')]
    print(f'\n{schema}.{table} metadata files:')
    for f in files:
        print(f'  {f}')

# Try to register with the v1 metadata file
print('\n=== Register tables via Trino CALL ===')
for schema, table in [('gold', 'dim_mahasiswa_fix'), ('gold', 'fact_khs_fix')]:
    # Find the latest metadata file
    prefix = f'iceberg/{schema}/{table}/metadata/'
    resp = s3.list_objects_v2(Bucket='warehouse', Prefix=prefix)
    meta_files = sorted([obj['Key'] for obj in resp.get('Contents', []) if obj['Key'].endswith('.json')])
    
    if meta_files:
        latest_meta = meta_files[-1]
        metadata_location = f's3a://warehouse/{latest_meta}'
        print(f'\n{schema}.{table}: registering with {latest_meta}')
        
        # Unregister first
        sql = f"CALL iceberg.system.unregister_table('{schema}', '{table}')"
        data = run_trino(sql)
        print(f'  Unregister: {data}')
        
        # Register
        sql = f"CALL iceberg.system.register_table('{schema}', '{table}', '{metadata_location}')"
        data = run_trino(sql)
        print(f'  Register: {data}')

# Verify
print('\n=== Verify tables ===')
for schema, table in [('gold', 'dim_mahasiswa_fix'), ('gold', 'fact_khs_fix')]:
    data = run_trino(f'SELECT count(*) FROM iceberg.{schema}.{table}')
    print(f'  {schema}.{table}: {data}')

# Show all gold tables again
print('\n=== SHOW TABLES IN iceberg.gold ===')
data = run_trino('SHOW TABLES IN iceberg.gold')
for row in data:
    print(f'  {row}')
