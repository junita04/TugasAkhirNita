from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Check Count")

bronze = spark.table(f"{ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa")
silver = spark.table(f"{ICEBERG_NAMESPACE}.silver.data_referensi_mahasiswa")
gold = spark.table(f"{ICEBERG_NAMESPACE}.gold.gold_mahasiswa")
training_dataset = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")

print("=" * 60)
print("JUMLAH DATA")
print("=" * 60)


print(f"Bronze : {bronze.count()}")
print(f"Silver : {silver.count()}")
print(f"Gold   : {gold.count()}")
print(f"Training Dataset : {training_dataset.count()}")

spark.stop()