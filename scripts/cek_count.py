from backend.spark.session import get_spark

spark = get_spark("Check Count")

bronze = spark.table("local.bronze.data_referensi_mahasiswa")
silver = spark.table("local.silver.data_referensi_mahasiswa")
gold = spark.table("local.gold.gold_mahasiswa")
training_dataset = spark.table("local.feature_store.training_dataset")

print("=" * 60)
print("JUMLAH DATA")
print("=" * 60)


print(f"Bronze : {bronze.count()}")
print(f"Silver : {silver.count()}")
print(f"Gold   : {gold.count()}")
print(f"Training Dataset : {training_dataset.count()}")

spark.stop()