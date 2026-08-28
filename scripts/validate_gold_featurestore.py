"""
COMPREHENSIVE GOLD + FEATURE STORE VALIDATION
================================================
Validasi semua tabel Gold dan Feature Store tanpa mengubah data.
"""
import sys
sys.path.insert(0, "/opt/airflow")

from pyspark.sql import functions as F
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Gold & Feature Store Validation")

SEP = "=" * 80

# ============================================================
# 1. GOLD LAYER VALIDATION
# ============================================================
print(SEP)
print("GOLD LAYER VALIDATION")
print(SEP)

gold_tables = {
    "dim_mahasiswa": f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa",
    "fact_khs": f"{ICEBERG_NAMESPACE}.gold.fact_khs",
    "gold_program_studi": f"{ICEBERG_NAMESPACE}.gold.gold_program_studi",
    "gold_kurikulum": f"{ICEBERG_NAMESPACE}.gold.gold_kurikulum",
}

for name, table in gold_tables.items():
    print(f"\n{'─' * 60}")
    print(f"TABLE: gold.{name}")
    print(f"{'─' * 60}")

    try:
        df = spark.table(table)

        # Location
        desc = spark.sql(f"DESCRIBE EXTENDED {table}").collect()
        loc = [list(row)[1] for row in desc if list(row)[0] == "Location"]
        loc = loc[0] if loc else "UNKNOWN"

        # Row count
        row_count = df.count()

        # Schema
        print(f"  Rows     : {row_count}")
        print(f"  Location : {loc}")
        print(f"  Columns  : {df.columns}")
        print(f"  Schema:")
        for field in df.schema.fields:
            print(f"    {field.name:<30} {field.dataType.simpleString():<20} nullable={field.nullable}")

        # NULL check
        print(f"\n  NULL check:")
        for col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            if null_count > 0:
                print(f"    {col}: {null_count} NULLs ({null_count/row_count*100:.1f}%)")
        if all(df.filter(F.col(c).isNull()).count() == 0 for c in df.columns):
            print(f"    No NULLs found")

        # Duplicate check (on primary key if applicable)
        if name == "dim_mahasiswa":
            distinct_id = df.select("id_mahasiswa").distinct().count()
            dup = row_count - distinct_id
            print(f"\n  Duplicate id_mahasiswa: {dup}")
        elif name == "fact_khs":
            distinct_id = df.select("id_mahasiswa").distinct().count()
            dup = row_count - distinct_id
            print(f"\n  Duplicate id_mahasiswa: {dup}")

        # Sample
        print(f"\n  Sample (first 3 rows):")
        df.show(3, truncate=False)

    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

# ============================================================
# 2. FEATURE STORE VALIDATION
# ============================================================
print(SEP)
print("FEATURE STORE VALIDATION")
print(SEP)

fs_tables = {
    "training_dataset": f"{ICEBERG_NAMESPACE}.feature_store.training_dataset",
    "inference_dataset": f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset",
}

for name, table in fs_tables.items():
    print(f"\n{'─' * 60}")
    print(f"TABLE: feature_store.{name}")
    print(f"{'─' * 60}")

    try:
        df = spark.table(table)

        # Location
        desc = spark.sql(f"DESCRIBE EXTENDED {table}").collect()
        loc = [list(row)[1] for row in desc if list(row)[0] == "Location"]
        loc = loc[0] if loc else "UNKNOWN"

        row_count = df.count()

        print(f"  Rows     : {row_count}")
        print(f"  Location : {loc}")
        print(f"  Columns  : {df.columns}")
        print(f"  Schema:")
        for field in df.schema.fields:
            print(f"    {field.name:<30} {field.dataType.simpleString():<20} nullable={field.nullable}")

        # NULL check
        print(f"\n  NULL check:")
        any_null = False
        for col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            if null_count > 0:
                print(f"    {col}: {null_count} NULLs ({null_count/row_count*100:.1f}%)")
                any_null = True
        if not any_null:
            print(f"    No NULLs found")

        # Duplicate check
        if "id_mahasiswa" in df.columns:
            distinct_id = df.select("id_mahasiswa").distinct().count()
            dup = row_count - distinct_id
            print(f"\n  Duplicate id_mahasiswa: {dup}")

        # Label distribution (for training)
        if "status_kelulusan" in df.columns:
            print(f"\n  Label distribution (status_kelulusan):")
            label_dist = df.groupBy("status_kelulusan").count().collect()
            for row in sorted(label_dist, key=lambda r: r[0]):
                pct = row["count"] / row_count * 100
                print(f"    {row['status_kelulusan']:<20} {row['count']:>6} ({pct:.1f}%)")

        # Numeric feature stats
        numeric_cols = [f.name for f in df.schema.fields if f.dataType.simpleString() in ("double", "int", "bigint")]
        if numeric_cols:
            print(f"\n  Numeric feature statistics:")
            for col in numeric_cols:
                stats = df.select(
                    F.min(col).alias("min"),
                    F.max(col).alias("max"),
                    F.avg(col).alias("mean"),
                    F.stddev(col).alias("stddev"),
                    F.expr(f"percentile_approx({col}, 0.5)").alias("median"),
                ).collect()[0]
                print(f"    {col:<20} min={stats['min']}, max={stats['max']}, "
                      f"mean={stats['mean']:.2f}, median={stats['median']}, stddev={stats['stddev']:.2f}")

        # Sample
        print(f"\n  Sample (first 5 rows):")
        df.show(5, truncate=False)

    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

# ============================================================
# 3. FEATURE COMPLETENESS CHECK
# ============================================================
print(SEP)
print("FEATURE COMPLETENESS FOR ML")
print(SEP)

expected_features_v2 = ["ip", "sks", "angkatan", "jumlah_mk"]
expected_label = "status_kelulusan"
optional_features = ["jenis_kelamin", "ipk", "total_sks"]

try:
    train = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
    infer = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")

    print("\nTraining Dataset:")
    print(f"  Columns: {train.columns}")

    print("\nInference Dataset:")
    print(f"  Columns: {infer.columns}")

    print(f"\nV2 Feature X: {expected_features_v2}")
    print(f"V2 Label: {expected_label}")

    print(f"\nFeature presence in Training:")
    for feat in expected_features_v2:
        present = feat in train.columns
        print(f"  {feat}: {'PRESENT' if present else 'MISSING'}")
    print(f"  {expected_label}: {'PRESENT' if expected_label in train.columns else 'MISSING'}")

    print(f"\nFeature presence in Inference:")
    for feat in expected_features_v2:
        present = feat in infer.columns
        print(f"  {feat}: {'PRESENT' if present else 'MISSING'}")

    print(f"\nOptional features (NOT in V2 Feature Store, expected):")
    for feat in optional_features:
        in_train = feat in train.columns
        in_infer = feat in infer.columns
        print(f"  {feat}: training={'YES' if in_train else 'NO'}, inference={'YES' if in_infer else 'NO'}")

except Exception as e:
    print(f"  ERROR: {e}")

# ============================================================
# 4. DATA LINEAGE CHECK: Gold -> Silver -> Bronze
# ============================================================
print(SEP)
print("DATA LINEAGE: Gold <- Silver <- Bronze")
print(SEP)

try:
    bronze_ref = spark.table(f"{ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa")
    silver_ref = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa")
    gold_dim = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")

    bronze_count = bronze_ref.count()
    silver_count = silver_ref.count()
    gold_count = gold_dim.count()

    print(f"\n  data_referensi_mahasiswa (Bronze): {bronze_count}")
    print(f"  silver_mahasiswa (Silver):         {silver_count}")
    print(f"  dim_mahasiswa (Gold):              {gold_count}")

    excluded_by_silver = bronze_count - silver_count
    excluded_by_gold = silver_count - gold_count

    print(f"\n  Bronze -> Silver excluded: {excluded_by_silver} rows "
          f"({excluded_by_silver/bronze_count*100:.1f}%)")
    print(f"  Silver -> Gold excluded:   {excluded_by_gold} rows "
          f"({excluded_by_gold/silver_count*100:.1f}%)")

    # Check KHS lineage
    bronze_khs = spark.table(f"{ICEBERG_NAMESPACE}.bronze.data_khs").count()
    silver_khs = spark.table(f"{ICEBERG_NAMESPACE}.silver.silver_khs").count()
    gold_fact = spark.table(f"{ICEBERG_NAMESPACE}.gold.fact_khs").count()

    print(f"\n  data_khs (Bronze):  {bronze_khs}")
    print(f"  silver_khs (Silver): {silver_khs}")
    print(f"  fact_khs (Gold):     {gold_fact}")

    excluded_khs_silver = bronze_khs - silver_khs
    excluded_khs_gold = silver_khs - gold_fact

    print(f"\n  Bronze -> Silver excluded: {excluded_khs_silver} rows")
    print(f"  Silver -> Gold excluded:   {excluded_khs_gold} rows")

except Exception as e:
    print(f"  ERROR: {e}")

spark.stop()
print(f"\n{SEP}")
print("VALIDATION COMPLETE")
print(SEP)
