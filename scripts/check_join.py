"""Check available features after JOIN."""
import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
import pyspark.sql.functions as F

spark = get_spark("check")

dim = spark.table("iceberg.gold.dim_mahasiswa")
fact = spark.table("iceberg.gold.fact_khs")

# Join
joined = dim.join(fact, on="id_mahasiswa", how="left")

# Check for sks_seharusnya and selisih_sks
# sks_seharusnya = jumlah_mk * 24 (24 SKS per MK)
# selisih_sks = total_sks - sks_seharusnya

joined = joined.withColumn("sks_seharusnya", F.col("jumlah_mk") * 24)
joined = joined.withColumn("selisih_sks", F.col("total_sks") - F.col("sks_seharusnya"))

print("=== Joined schema ===")
joined.printSchema()
print(f"Rows: {joined.count()}")
joined.show(3, truncate=False)

# Check nulls in key columns
print("\n=== Null counts ===")
for col_name in ["jenis_kelamin", "ip", "ipk", "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks"]:
    null_count = joined.filter(F.col(col_name).isNull()).count()
    print(f"  {col_name}: {null_count} nulls")

# Check distinct mahasiswa
total = joined.count()
distinct = joined.select("id_mahasiswa").distinct().count()
print(f"\nTotal rows: {total}")
print(f"Distinct id: {distinct}")
print(f"Duplicates: {total - distinct}")
