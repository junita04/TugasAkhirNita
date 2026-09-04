"""
Audit pipeline: trace 257 missing inference students.
Gold -> Feature Store -> Inference -> Iceberg Output
"""
import sys
sys.path.insert(0, "/opt/airflow")

from pyspark.sql import functions as F
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE
from backend.feature_store.feature_engineering import FEATURE_X

spark = get_spark("Audit Pipeline")

EXPECTED = {2022: 4109, 2023: 4046, 2024: 4346}
EXPECTED_TOTAL = sum(EXPECTED.values())

print("=" * 70)
print("PIPELINE AUDIT — RECONCILIATION")
print("=" * 70)

# =========================================================
# 1. GOLD LAYER
# =========================================================
print("\n### 1. GOLD LAYER (dim_mahasiswa)")
gold = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")

gold_aktif = gold.filter(
    (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF")
    & (F.col("angkatan").isin(2022, 2023, 2024))
)
gold_total = gold_aktif.count()
print(f"  Total AKTIF 2022-2024: {gold_total}")

gold_by_ang = {}
for a in [2022, 2023, 2024]:
    c = gold_aktif.filter(F.col("angkatan") == a).count()
    gold_by_ang[a] = c
    delta = c - EXPECTED[a]
    status = "OK" if delta == 0 else f"DELTA={delta}"
    print(f"  Angkatan {a}: {c} (expected {EXPECTED[a]}) {status}")

# Check NULL ip
null_ip = gold_aktif.filter(F.col("ip").isNull())
null_ip_count = null_ip.count()
print(f"\n  NULL ip in Gold AKTIF: {null_ip_count}")

null_ip_by_ang = {}
for a in [2022, 2023, 2024]:
    c = null_ip.filter(F.col("angkatan") == a).count()
    null_ip_by_ang[a] = c
    if c > 0:
        print(f"    Angkatan {a}: {c} NULL ip")

# =========================================================
# 2. FEATURE STORE INFERENCE DATASET
# =========================================================
print("\n### 2. FEATURE STORE INFERENCE DATASET")
inference_table = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")
fs_total = inference_table.count()
print(f"  Total: {fs_total}")

fs_by_ang = {}
for a in [2022, 2023, 2024]:
    c = inference_table.filter(F.col("angkatan") == a).count()
    fs_by_ang[a] = c
    delta = c - gold_by_ang[a]
    status = "OK" if delta == 0 else f"LOST {abs(delta)}"
    print(f"  Angkatan {a}: {c} (from Gold {gold_by_ang[a]}) {status}")

fs_lost = gold_total - fs_total
print(f"  TOTAL LOST Gold -> Feature Store: {fs_lost}")

# Find which IDs were lost
gold_ids = set(r["id_mahasiswa"] for r in gold_aktif.select("id_mahasiswa").collect())
fs_ids = set(r["id_mahasiswa"] for r in inference_table.select("id_mahasiswa").collect())
lost_ids = gold_ids - fs_ids
print(f"  Lost IDs count: {len(lost_ids)}")

if lost_ids:
    lost_df = gold_aktif.filter(F.col("id_mahasiswa").isin(list(lost_ids)[:100]))
    print(f"\n  Sample lost IDs (up to 5):")
    lost_df.select("id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk").show(5)

    # Check if all lost have NULL ip
    lost_all = gold_aktif.filter(F.col("id_mahasiswa").isin(list(lost_ids)))
    lost_null_ip = lost_all.filter(F.col("ip").isNull()).count()
    print(f"  Lost IDs with NULL ip: {lost_null_ip} / {len(lost_ids)}")

    # Check angkatan distribution of lost
    for a in [2022, 2023, 2024]:
        c = lost_all.filter(F.col("angkatan") == a).count()
        if c > 0:
            print(f"    Lost from angkatan {a}: {c}")

# =========================================================
# 3. ML INFERENCE (prediction results)
# =========================================================
print("\n### 3. ML INFERENCE (prediction parquet)")
import pandas as pd
pred = pd.read_parquet("/opt/airflow/data/predictions/prediction_result_without_smote.parquet")
ml_total = len(pred)
print(f"  Total predictions: {ml_total}")

ml_by_ang = pred.groupby("angkatan").size()
for a in [2022, 2023, 2024]:
    c = int(ml_by_ang.get(a, 0))
    delta = c - fs_by_ang.get(a, 0)
    status = "OK" if delta == 0 else f"DELTA={delta}"
    print(f"  Angkatan {a}: {c} (from Feature Store {fs_by_ang.get(a, 0)}) {status}")

# =========================================================
# 4. ICEBERG OUTPUT
# =========================================================
print("\n### 4. ICEBERG OUTPUT (prediction_result_without_smote)")
iceberg = spark.table("hive_iceberg.feature_store.prediction_result_without_smote")
ice_total = iceberg.count()
print(f"  Total: {ice_total}")

ice_by_ang = {}
for a in [2022, 2023, 2024]:
    c = iceberg.filter(F.col("angkatan") == a).count()
    ice_by_ang[a] = c
    delta = c - ml_by_ang.get(a, 0)
    status = "OK" if delta == 0 else f"DELTA={delta}"
    print(f"  Angkatan {a}: {c} (from ML {int(ml_by_ang.get(a, 0))}) {status}")

# =========================================================
# 5. RECONCILIATION TABLE
# =========================================================
print("\n" + "=" * 70)
print("RECONCILIATION TABLE")
print("=" * 70)
header = f"{'Tahap':<25} {'2022':>8} {'2023':>8} {'2024':>8} {'Total':>8}"
print(header)
print("-" * 70)
print(f"{'Gold (AKTIF)':<25} {gold_by_ang[2022]:>8} {gold_by_ang[2023]:>8} {gold_by_ang[2024]:>8} {gold_total:>8}")
print(f"{'Feature Store':<25} {fs_by_ang[2022]:>8} {fs_by_ang[2023]:>8} {fs_by_ang[2024]:>8} {fs_total:>8}")
print(f"{'ML Inference':<25} {int(ml_by_ang.get(2022,0)):>8} {int(ml_by_ang.get(2023,0)):>8} {int(ml_by_ang.get(2024,0)):>8} {ml_total:>8}")
print(f"{'Iceberg Output':<25} {ice_by_ang[2022]:>8} {ice_by_ang[2023]:>8} {ice_by_ang[2024]:>8} {ice_total:>8}")
print(f"{'Expected':<25} {EXPECTED[2022]:>8} {EXPECTED[2023]:>8} {EXPECTED[2024]:>8} {EXPECTED_TOTAL:>8}")
print("=" * 70)

# =========================================================
# 6. ROOT CAUSE
# =========================================================
print("\n### ROOT CAUSE ANALYSIS")
print(f"  Gold AKTIF 2022-2024: {gold_total}")
print(f"  Feature Store:       {fs_total}")
print(f"  Missing:             {gold_total - fs_total}")
print()
print("  Pipeline code (inference_dataset.py, line 98):")
print("    valid = aktif.dropna(subset=FEATURE_X)")
print()
print(f"  FEATURE_X = {FEATURE_X}")
print()
print(f"  Students with NULL ip in Gold: {null_ip_count}")
print(f"  Students lost to Feature Store: {fs_lost}")
print(f"  Match: {'YES' if null_ip_count == fs_lost else 'NO'}")
print()
print("  ROOT CAUSE: dropna(subset=FEATURE_X) removes students with")
print("  ip=NULL because ip is in FEATURE_X. These 257 students have")
print("  no KHS records, so ip is NULL after LEFT JOIN.")

spark.stop()
