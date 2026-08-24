import os, sys
os.environ['SPARK_EVENT_LOG'] = 'false'
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName('Readonly-Validate-MinIO-3') \
    .master('local[*]') \
    .config('spark.driver.extraClassPath', '/opt/airflow/jars/*') \
    .config('spark.sql.catalog.iceberg', 'org.apache.iceberg.spark.SparkCatalog') \
    .config('spark.sql.catalog.iceberg.type', 'hadoop') \
    .config('spark.sql.catalog.iceberg.warehouse', 's3a://warehouse/iceberg') \
    .config('spark.hadoop.fs.s3a.endpoint', 'http://minio:9000') \
    .config('spark.hadoop.fs.s3a.access.key', 'minioadmin') \
    .config('spark.hadoop.fs.s3a.secret.key', 'minioadmin-password') \
    .config('spark.hadoop.fs.s3a.path.style.access', 'true') \
    .config('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem') \
    .getOrCreate()

spark.sparkContext.setLogLevel('WARN')

try:
    df = spark.read.format('iceberg').load('iceberg.bronze.data_referensi_mahasiswa')
    print('SCHEMA OK')
    print('COLUMNS: %s' % str(df.columns))
    cnt = df.count()
    print('COUNT: %d' % cnt)
except Exception as e:
    import traceback
    traceback.print_exc()

spark.stop()
