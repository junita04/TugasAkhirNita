"""
Cleanup script: Fix Iceberg table locations.
Drops Silver tables with stale file:///D:/... locations.
Fixes data_referensi_mahasiswa in Bronze if missing.
"""
import sys
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_CATALOG, ICEBERG_NAMESPACE

spark = get_spark("Iceberg Cleanup")

print("=" * 60)
print("STEP 1: Drop Silver tables with stale file:/// locations")
print("=" * 60)

silver_tables = [
    "silver_khs", "silver_mahasiswa", "silver_program_studi",
    "silver_kelas", "silver_kurikulum",
    "data_referensi_mahasiswa", "data_kelas", "data_khs",
    "data_program_studi", "data_kurikulum",
    "silver_khs_lama", "silver_mahasiswa_lama", "silver_program_studi_lama",
    "silver_kelas_lama", "silver_kurikulum_lama",
]

for tbl in silver_tables:
    try:
        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.silver.{tbl}")
        print(f"  DROPPED: silver.{tbl}")
    except Exception as e:
        print(f"  SKIP: silver.{tbl} ({e})")

print()
print("=" * 60)
print("STEP 2: Check & Fix data_referensi_mahasiswa in Bronze")
print("=" * 60)

# Check if table exists
try:
    rows = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze").collect()
    bronze_tables = [list(r)[1] for r in rows]
    print(f"  Bronze tables: {bronze_tables}")

    if "data_referensi_mahasiswa" not in bronze_tables:
        print("  data_referensi_mahasiswa NOT in bronze. Checking S3...")

        # Check if Iceberg data files exist in S3
        from py4j.java_gateway import java_import
        hadoop = spark._jvm.org.apache.hadoop.fs.FileSystem
        fs = hadoop.get(spark._jvm.java.net.URI.create("s3a://warehouse"), spark._jvm.org.apache.hadoop.conf.Configuration())

        # Try to list the table path in S3
        s3_path = spark._jvm.org.apache.hadoop.fs.Path("s3a://warehouse/iceberg/bronze/data_referensi_mahasiswa")
        exists = fs.exists(s3_path)
        print(f"  S3 path exists: {exists}")

        if exists:
            print("  Data exists in S3. Registering table in metastore...")
            spark.sql(f"""
                CREATE TABLE IF NOT EXISTS {ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa
                USING iceberg
                LOCATION 's3a://warehouse/iceberg/bronze/data_referensi_mahasiswa'
            """)
            print("  REGISTERED: bronze.data_referensi_mahasiswa")
        else:
            print("  S3 data NOT found. Table needs to be re-created by Bronze task.")
    else:
        # Check its location
        try:
            desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa").collect()
            for row in desc:
                if list(row)[0] == "Location":
                    loc = list(row)[1]
                    print(f"  data_referensi_mahasiswa location: {loc}")
                    if loc.startswith("file:"):
                        print("  WRONG LOCATION! Dropping and re-registering...")
                        spark.sql(f"DROP TABLE IF EXISTS {ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa")
                        spark.sql(f"""
                            CREATE TABLE IF NOT EXISTS {ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa
                            USING iceberg
                            LOCATION 's3a://warehouse/iceberg/bronze/data_referensi_mahasiswa'
                        """)
                        print("  RE-REGISTERED: bronze.data_referensi_mahasiswa")
        except Exception as e:
            print(f"  Location check error: {e}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=" * 60)
print("STEP 3: Verify final state")
print("=" * 60)

# Verify silver namespace is clean
try:
    rows = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.silver").collect()
    if rows:
        print(f"  WARNING: Silver still has {len(rows)} tables")
        for r in rows:
            print(f"    {list(r)}")
    else:
        print("  Silver namespace: EMPTY (ready for fresh tables)")
except Exception as e:
    print(f"  Silver check error: {e}")

# Verify bronze
try:
    rows = spark.sql(f"SHOW TABLES IN {ICEBERG_NAMESPACE}.bronze").collect()
    print(f"  Bronze tables: {len(rows)}")
    for r in rows:
        tbl_name = list(r)[1]
        desc = spark.sql(f"DESCRIBE EXTENDED {ICEBERG_NAMESPACE}.bronze.{tbl_name}").collect()
        for row in desc:
            if list(row)[0] == "Location":
                print(f"    {tbl_name}: {list(row)[1]}")
except Exception as e:
    print(f"  Bronze check error: {e}")

spark.stop()
print()
print("DONE. Silver tables dropped. Bronze verified.")
