import sys
from pyspark.sql import SparkSession

HMS_URI = sys.argv[1] if len(sys.argv) > 1 else "thrift://hms313-fresh:9083"
WAREHOUSE = sys.argv[2] if len(sys.argv) > 2 else "s3a://warehouse/hms313-compat"
NS = sys.argv[3] if len(sys.argv) > 3 else "hmsfresh"
PROD_META = sys.argv[4] if len(sys.argv) > 4 else ""

print("=" * 70)
print(f"HMS_URI   : {HMS_URI}")
print(f"WAREHOUSE : {WAREHOUSE}")
print(f"NS        : {NS}")
print("=" * 70)

builder = (
    SparkSession.builder
    .appName("hms313-fresh-test")
    .master("local[2]")
    .config("spark.driver.memory", "1g")
    .config("spark.driver.host", "127.0.0.1")
    .config("spark.driver.bindAddress", "127.0.0.1")
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.executor.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.eventLog.enabled", "false")
    # S3A (MinIO)
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    # Map s3:// -> S3A (production metadata_location uses s3:// from Trino)
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    # Hadoop catalog (secondary)
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hadoop")
    .config("spark.sql.catalog.iceberg.warehouse", WAREHOUSE)
    # HMS-backed catalog
    .config("spark.sql.catalog.hive_iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.hive_iceberg.type", "hive")
    .config("spark.sql.catalog.hive_iceberg.uri", HMS_URI)
    .config("spark.sql.catalog.hive_iceberg.warehouse", WAREHOUSE)
    .config("spark.sql.catalog.hive_iceberg.cache-enabled", "false")
)

spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("WARN")

results = {}

def step(name, fn):
    print("\n" + "-" * 70)
    print(f"STEP: {name}")
    try:
        r = fn()
        results[name] = ("OK", r)
        print(f"RESULT {name}: OK -> {r}")
    except Exception as e:
        results[name] = ("FAIL", f"{type(e).__name__}: {e}")
        print(f"RESULT {name}: FAIL -> {type(e).__name__}: {e}")

# 1. namespaces
def s_ns():
    rows = spark.sql("SHOW NAMESPACES IN hive_iceberg").collect()
    return sorted([r[0] for r in rows])
step("list_namespaces", s_ns)

# 2. create namespaces
def s_mkns():
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS hive_iceberg.{NS}")
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS iceberg.{NS}")
    return "created"
step("create_namespace", s_mkns)

# 3. write test table (exercises Iceberg HMS lock()/commit)
def s_write():
    spark.sql(f"DROP TABLE IF EXISTS hive_iceberg.{NS}.compat_fresh")
    spark.sql(f"CREATE TABLE hive_iceberg.{NS}.compat_fresh (id INT, val STRING) USING iceberg")
    spark.sql(f"INSERT INTO hive_iceberg.{NS}.compat_fresh VALUES (1,'a'),(2,'b'),(3,'c')")
    return "wrote 3 rows"
step("write_and_commit", s_write)

# 4. read back
def s_read():
    c = spark.sql(f"SELECT count(*) AS c FROM hive_iceberg.{NS}.compat_fresh").collect()[0]["c"]
    loc = spark.sql(f"DESCRIBE EXTENDED hive_iceberg.{NS}.compat_fresh").filter("col_name='Location'").collect()
    locv = loc[0]["data_type"] if loc else "?"
    return f"count={c}, location={locv}"
step("read_back", s_read)

# 5. read-only register of a production table (uses s3:// metadata)
if PROD_META:
    def s_register():
        spark.sql(f"DROP TABLE IF EXISTS hive_iceberg.{NS}.prod_ref")
        spark.sql(f"CALL hive_iceberg.system.register_table(table => '{NS}.prod_ref', metadata_file => '{PROD_META}')")
        c = spark.sql(f"SELECT count(*) AS c FROM hive_iceberg.{NS}.prod_ref").collect()[0]["c"]
        return f"registered, count={c}"
    step("register_and_read_prod", s_register)

print("\n" + "=" * 70)
print("SUMMARY")
for k, v in results.items():
    print(f"  {v[0]:4}  {k}: {v[1]}")
print("=" * 70)
spark.stop()
