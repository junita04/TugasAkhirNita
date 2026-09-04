"""
AUDIT JUMLAH DATA - READ-ONLY CHECK
====================================
Script ini hanya membaca data, TIDAK mengubah apapun.
"""

import sys
sys.path.insert(0, '/opt/airflow')

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

def audit_table(spark, full_table_name, has_id_mahasiswa=True):
    """Audit satu tabel: count, distinct id, null id, duplicate id."""
    try:
        df = spark.table(full_table_name)
        row_count = df.count()

        if has_id_mahasiswa:
            distinct_count = df.select("id_mahasiswa").distinct().count()
            null_id = df.filter(df["id_mahasiswa"].isNull()).count()
            duplicate_id = row_count - distinct_id if (distinct_id := distinct_count) else 0
        else:
            distinct_count = None
            null_id = None
            duplicate_id = None

        return {
            "table": full_table_name,
            "row_count": row_count,
            "distinct_id": distinct_count,
            "null_id": null_id,
            "duplicate_id": duplicate_id,
        }
    except Exception as e:
        return {
            "table": full_table_name,
            "row_count": f"ERROR: {e}",
            "distinct_id": None,
            "null_id": None,
            "duplicate_id": None,
        }

def main():
    spark = get_spark("TugasAkhirNita - Data Count Audit")

    print("=" * 80)
    print("DATA COUNT AUDIT - READ ONLY")
    print("=" * 80)
    print(f"ICEBERG_NAMESPACE: {ICEBERG_NAMESPACE}")
    print()

    # ============================================================
    # 1. BRONZE LAYER
    # ============================================================
    print("=" * 80)
    print("1. BRONZE LAYER")
    print("=" * 80)

    bronze_tables = [
        f"{ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa",
        f"{ICEBERG_NAMESPACE}.bronze.data_khs",
        f"{ICEBERG_NAMESPACE}.bronze.data_program_studi",
        f"{ICEBERG_NAMESPACE}.bronze.data_mata_kuliah",
        f"{ICEBERG_NAMESPACE}.bronze.data_kelas",
        f"{ICEBERG_NAMESPACE}.bronze.data_kurikulum",
    ]

    bronze_results = []
    for table in bronze_tables:
        has_id = "referensi_mahasiswa" in table or "khs" in table
        result = audit_table(spark, table, has_id_mahasiswa=has_id)
        bronze_results.append(result)
        print(f"\n  Table: {table}")
        print(f"    Row Count      : {result['row_count']}")
        if result['distinct_id'] is not None:
            print(f"    Distinct ID    : {result['distinct_id']}")
            print(f"    NULL ID        : {result['null_id']}")
            print(f"    Duplicate ID   : {result['duplicate_id']}")

    # ============================================================
    # 2. SILVER LAYER
    # ============================================================
    print()
    print("=" * 80)
    print("2. SILVER LAYER")
    print("=" * 80)

    silver_tables = [
        f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa",
        f"{ICEBERG_NAMESPACE}.silver.silver_khs",
        f"{ICEBERG_NAMESPACE}.silver.silver_program_studi",
        f"{ICEBERG_NAMESPACE}.silver.silver_kelas",
        f"{ICEBERG_NAMESPACE}.silver.silver_kurikulum",
    ]

    silver_results = []
    for table in silver_tables:
        has_id = "mahasiswa" in table or "khs" in table
        result = audit_table(spark, table, has_id_mahasiswa=has_id)
        silver_results.append(result)
        print(f"\n  Table: {table}")
        print(f"    Row Count      : {result['row_count']}")
        if result['distinct_id'] is not None:
            print(f"    Distinct ID    : {result['distinct_id']}")
            print(f"    NULL ID        : {result['null_id']}")
            print(f"    Duplicate ID   : {result['duplicate_id']}")

    # ============================================================
    # 3. GOLD LAYER
    # ============================================================
    print()
    print("=" * 80)
    print("3. GOLD LAYER")
    print("=" * 80)

    gold_tables = [
        f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa",
        f"{ICEBERG_NAMESPACE}.gold.fact_khs",
    ]

    gold_results = []
    for table in gold_tables:
        result = audit_table(spark, table, has_id_mahasiswa=True)
        gold_results.append(result)
        print(f"\n  Table: {table}")
        print(f"    Row Count      : {result['row_count']}")
        print(f"    Distinct ID    : {result['distinct_id']}")
        print(f"    NULL ID        : {result['null_id']}")
        print(f"    Duplicate ID   : {result['duplicate_id']}")

    # ============================================================
    # 4. REKONSILIASI - DATA MAHASISWA
    # ============================================================
    print()
    print("=" * 80)
    print("4. REKONSILIASI - DATA MAHASISWA")
    print("=" * 80)

    # Find the specific results
    bronze_mahasiswa = next((r for r in bronze_results if "referensi_mahasiswa" in r["table"]), None)
    silver_mahasiswa = next((r for r in silver_results if "silver_mahasiswa" in r["table"]), None)
    gold_dim = next((r for r in gold_results if "dim_mahasiswa" in r["table"]), None)

    if bronze_mahasiswa and silver_mahasiswa and gold_dim:
        b_count = bronze_mahasiswa["row_count"]
        b_distinct = bronze_mahasiswa["distinct_id"]
        s_count = silver_mahasiswa["row_count"]
        s_distinct = silver_mahasiswa["distinct_id"]
        g_count = gold_dim["row_count"]
        g_distinct = gold_dim["distinct_id"]

        print(f"\n  Bronze (data_referensi_mahasiswa):")
        print(f"    COUNT(*)           : {b_count}")
        print(f"    COUNT(DISTINCT ID) : {b_distinct}")

        print(f"\n  Silver (silver_mahasiswa):")
        print(f"    COUNT(*)           : {s_count}")
        print(f"    COUNT(DISTINCT ID) : {s_distinct}")

        print(f"\n  Gold (dim_mahasiswa):")
        print(f"    COUNT(*)           : {g_count}")
        print(f"    COUNT(DISTINCT ID) : {g_distinct}")

        # Rekonsiliasi
        print()
        print("  REKONSILIASI:")
        print(f"  Bronze -> Silver:")
        print(f"    Jumlah masuk (Bronze)  : {b_count}")
        print(f"    Jumlah keluar (Silver) : {s_count}")
        print(f"    Selisih                : {s_count - b_count}")
        print(f"    Penjelasan             : Filtering data invalid + drop duplicates")

        print(f"\n  Silver -> Gold:")
        print(f"    Jumlah masuk (Silver)  : {s_count}")
        print(f"    Jumlah keluar (Gold)   : {g_count}")
        print(f"    Selisih                : {g_count - s_count}")
        print(f"    Penjelasan             : LEFT JOIN dengan fact_khs + dropDuplicates")

        print(f"\n  Bronze -> Gold:")
        print(f"    Jumlah masuk (Bronze)  : {b_count}")
        print(f"    Jumlah keluar (Gold)   : {g_count}")
        print(f"    Selisih                : {g_count - b_count}")

    # ============================================================
    # 5. INVESTIGASI DATA YANG HILANG
    # ============================================================
    print()
    print("=" * 80)
    print("5. INVESTIGASI DATA YANG HILANG")
    print("=" * 80)

    if bronze_mahasiswa and silver_mahasiswa and gold_dim:
        # Get all IDs from each layer
        bronze_ids = set(
            row[0] for row in spark.table(bronze_mahasiswa["table"])
            .select("id_mahasiswa").collect()
        )
        silver_ids = set(
            row[0] for row in spark.table(silver_mahasiswa["table"])
            .select("id_mahasiswa").collect()
        )
        gold_ids = set(
            row[0] for row in spark.table(gold_dim["table"])
            .select("id_mahasiswa").collect()
        )

        # Find missing IDs
        bronze_minus_silver = bronze_ids - silver_ids
        silver_minus_gold = silver_ids - gold_ids
        bronze_minus_gold = bronze_ids - gold_ids

        print(f"\n  BRONZE -> SILVER:")
        print(f"    Jumlah ID di Bronze tapi tidak di Silver: {len(bronze_minus_silver)}")
        if bronze_minus_silver:
            print(f"    Contoh ID yang hilang: {list(bronze_minus_silver)[:10]}")

        print(f"\n  SILVER -> GOLD:")
        print(f"    Jumlah ID di Silver tapi tidak di Gold: {len(silver_minus_gold)}")
        if silver_minus_gold:
            print(f"    Contoh ID yang hilang: {list(silver_minus_gold)[:10]}")

        print(f"\n  BRONZE -> GOLD:")
        print(f"    Jumlah ID di Bronze tapi tidak di Gold: {len(bronze_minus_gold)}")
        if bronze_minus_gold:
            print(f"    Contoh ID yang hilang: {list(bronze_minus_gold)[:10]}")

    # ============================================================
    # 6. SUMMARY TABLE
    # ============================================================
    print()
    print("=" * 80)
    print("6. SUMMARY TABLE")
    print("=" * 80)
    print()
    print(f"{'Layer':<20} {'Table':<35} {'Row Count':>12} {'Distinct ID':>14} {'NULL ID':>10} {'Dup ID':>10}")
    print("-" * 100)

    for r in bronze_results:
        print(f"{'Bronze':<20} {r['table'].split('.')[-1]:<35} {r['row_count']:>12} {str(r['distinct_id']):>14} {str(r['null_id']):>10} {str(r['duplicate_id']):>10}")

    for r in silver_results:
        print(f"{'Silver':<20} {r['table'].split('.')[-1]:<35} {r['row_count']:>12} {str(r['distinct_id']):>14} {str(r['null_id']):>10} {str(r['duplicate_id']):>10}")

    for r in gold_results:
        print(f"{'Gold':<20} {r['table'].split('.')[-1]:<35} {r['row_count']:>12} {str(r['distinct_id']):>14} {str(r['null_id']):>10} {str(r['duplicate_id']):>10}")

    print()
    print("=" * 80)
    print("AUDIT SELESAI - TIDAK ADA PERUBAHAN DATA")
    print("=" * 80)

    spark.stop()

if __name__ == "__main__":
    main()
