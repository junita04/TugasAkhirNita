import sys
import traceback

sys.path.insert(0, "/opt/airflow")

results = {}


def step(name, fn):
    try:
        r = fn()
        print(f"[OK]   {name}: {r}", flush=True)
        results[name] = "OK"
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {name}: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        results[name] = f"FAIL {type(e).__name__}"


from backend.config import settings as S  # noqa: E402

print(
    "CONFIG: SPARK_MODE=%s MASTER=%s ICEBERG_CATALOG=%s ICEBERG_WAREHOUSE=%s HMS=%s PIPELINE_NS=%s"
    % (
        S.SPARK_MODE,
        S.MASTER,
        S.ICEBERG_CATALOG,
        S.ICEBERG_WAREHOUSE,
        S.HIVE_METASTORE_URI,
        __import__("os").environ.get("PIPELINE_NS"),
    ),
    flush=True,
)

from backend.spark.session import get_spark  # noqa: E402

spark = get_spark("hms313-compat-test")

step(
    "list_namespaces",
    lambda: sorted(r[0] for r in spark.sql("SHOW NAMESPACES IN hive_iceberg").collect()),
)

# 2. Exact operation that failed under HMS 4.2.1 (uses get_table_objects_by_name)
step(
    "show_tables_prod_bronze",
    lambda: sorted(r[1] for r in spark.sql("SHOW TABLES IN hive_iceberg.bronze").collect()),
)

# 3. get_table path (Iceberg loadTable) - READ ONLY on a production table
step(
    "read_prod_table_count",
    lambda: spark.table("hive_iceberg.bronze.data_referensi_mahasiswa").count(),
)

# 4. Write a brand-new test table in the throwaway namespace / test warehouse
test_tbl = "hive_iceberg.hmscompat_bronze.compat_test_table"


def write_test():
    spark.sql("CREATE NAMESPACE IF NOT EXISTS hive_iceberg.hmscompat_bronze")
    spark.sql(f"DROP TABLE IF EXISTS {test_tbl}")
    from pyspark.sql import Row

    df = spark.createDataFrame([Row(id=1, val="a"), Row(id=2, val="b")])
    df.writeTo(test_tbl).using("iceberg").createOrReplace()
    return "write+commit OK"


step("write_test_table", write_test)

# 5. Read it back
step(
    "read_test_table",
    lambda: sorted((r.id, r.val) for r in spark.table(test_tbl).collect()),
)

# 6. Confirm the new table is registered in the THROWAWAY HMS
step(
    "show_tables_hmscompat_bronze",
    lambda: sorted(r[1] for r in spark.sql("SHOW TABLES IN hive_iceberg.hmscompat_bronze").collect()),
)

# 7. Confirm the registered location is the test warehouse (isolation proof)
step(
    "test_table_location",
    lambda: spark.sql(f"DESCRIBE EXTENDED {test_tbl}").filter("col_name = 'Location'").collect()[0][1],
)

try:
    spark.stop()
except Exception:
    pass

print("RESULT:", results, flush=True)
