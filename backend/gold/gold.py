from pyspark.sql import functions as F

from backend.gold.gold_mahasiswa import process_gold_dim_mahasiswa
from backend.gold.gold_fact_khs import process_gold_fact_khs
from backend.gold.gold_prodi import process_gold_program_studi
from backend.gold.gold_kurikulum import process_gold_kurikulum

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _validate_star_schema():

    spark = get_spark("TugasAkhirNita - Gold Validation")

    dim = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")
    fact = spark.table(f"{ICEBERG_NAMESPACE}.gold.fact_khs")

    print()
    print("=" * 88)
    print("VALIDASI GOLD STAR SCHEMA")
    print("=" * 88)

    dim_total = dim.count()
    dim_distinct = dim.select("id_mahasiswa").distinct().count()
    dim_dup = dim_total - dim_distinct
    dim_null_pk = dim.filter(F.col("id_mahasiswa").isNull()).count()

    fact_total = fact.count()
    fact_distinct = fact.select("id_mahasiswa").distinct().count()
    fact_dup = fact_total - fact_distinct
    fact_null_id = fact.filter(F.col("id_mahasiswa").isNull()).count()
    fact_null_ip = fact.filter(F.col("ip").isNull()).count()
    fact_null_sks = fact.filter(F.col("sks").isNull()).count()

    print(f"# DIM_MAHASISWA")
    print(f"  row count            : {dim_total}")
    print(f"  distinct id          : {dim_distinct}")
    print(f"  duplicate id         : {dim_dup}")
    print(f"  null primary key     : {dim_null_pk}")

    print()
    print(f"# FACT_KHS")
    print(f"  row count            : {fact_total}")
    print(f"  distinct id          : {fact_distinct}")
    print(f"  duplicate id         : {fact_dup}")
    print(f"  null id_mahasiswa    : {fact_null_id}")
    print(f"  null IP              : {fact_null_ip}")
    print(f"  null SKS             : {fact_null_sks}")

    # =====================================================
    # Referential Integrity
    # =====================================================

    orphan_fact = (
        fact.select("id_mahasiswa")
        .join(dim.select("id_mahasiswa"), ["id_mahasiswa"], "left_anti")
        .count()
    )
    dim_without_fact = (
        dim.select("id_mahasiswa")
        .join(fact.select("id_mahasiswa"), ["id_mahasiswa"], "left_anti")
        .count()
    )

    print()
    print(f"# REFERENTIAL INTEGRITY")
    print(f"  fact tanpa dim (orphan): {orphan_fact}")
    print(f"  dim tanpa fact         : {dim_without_fact}")

    # =====================================================
    # JOIN VALIDATION (LEFT JOIN dim -> fact)
    # =====================================================

    joined = dim.join(fact, on="id_mahasiswa", how="left")
    join_total = joined.count()

    row_multiplication = join_total - dim_total

    matched = joined.filter(F.col("ip").isNotNull()).count()
    non_matched = join_total - matched

    print()
    print(f"# JOIN VALIDATION (dim LEFT JOIN fact)")
    print(f"  row count hasil join  : {join_total}")
    print(f"  matching (ada fact)   : {matched}")
    print(f"  non-matching(no fact) : {non_matched}")
    print(f"  row multiplication    : {row_multiplication}")

    print()
    print("GRAIN VALIDATION")
    print(f"  dim 1 mahasiswa = 1 row : {'PASS' if dim_total == dim_distinct else 'FAIL'}")
    print(f"  fact 1 mahasiswa = 1 row: {'PASS' if fact_total == fact_distinct else 'FAIL'}")

    print()
    print("REFERENTIAL INTEGRITY : "
          f"{'PASS' if orphan_fact == 0 else 'FAIL'}")
    print("GRAIN VALIDATION      : "
          f"{'PASS' if (dim_total == dim_distinct and fact_total == fact_distinct) else 'FAIL'}")
    print("JOIN VALIDATION       : "
          f"{'PASS' if row_multiplication == 0 else 'FAIL'}")
    print("=" * 88)

    return {
        "dim_total": dim_total,
        "dim_distinct": dim_distinct,
        "dim_dup": dim_dup,
        "dim_null_pk": dim_null_pk,
        "fact_total": fact_total,
        "fact_distinct": fact_distinct,
        "fact_dup": fact_dup,
        "fact_null_id": fact_null_id,
        "fact_null_ip": fact_null_ip,
        "fact_null_sks": fact_null_sks,
        "orphan_fact": orphan_fact,
        "dim_without_fact": dim_without_fact,
        "join_total": join_total,
        "matched": matched,
        "non_matched": non_matched,
        "row_multiplication": row_multiplication,
    }


def process_gold():

    logger.info("=" * 60)
    logger.info("Memulai Proses Gold Layer (Star Schema)")
    logger.info("=" * 60)

    process_gold_dim_mahasiswa()

    process_gold_fact_khs()

    process_gold_program_studi()

    process_gold_kurikulum()

    result = _validate_star_schema()

    logger.info("=" * 60)
    logger.info("Seluruh Gold Layer berhasil dibuat.")
    logger.info("=" * 60)

    return result