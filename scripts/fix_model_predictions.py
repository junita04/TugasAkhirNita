"""Rebuild model_predictions table with correct inference data only."""
import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

ns = ICEBERG_NAMESPACE
spark = get_spark("Rebuild model_predictions")

# Read correct inference predictions from parquet
inference_df = pd.read_parquet('/opt/airflow/results/prediction_final.parquet')
print(f"Prediction parquet: {len(inference_df)} rows")
print(f"Angkatan dist: {dict(inference_df['angkatan'].value_counts().sort_index())}")
print(f"Label dist: {dict(inference_df['prediksi_label'].value_counts())}")

# Drop and recreate table
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.model_predictions")
spark.sql(f"""CREATE TABLE {ns}.gold.model_predictions (
    id_mahasiswa STRING,
    angkatan INT,
    prediksi STRING,
    probability DOUBLE
)""")

# Write in batches
batch_size = 3000
total = len(inference_df)
for start in range(0, total, batch_size):
    batch = inference_df.iloc[start:start+batch_size]
    mp_rows = []
    for _, r in batch.iterrows():
        pred = 'Tepat Waktu' if r['prediksi_label'] == 0 else 'Terlambat'
        prob = float(r['probability_tepat_waktu'])
        mp_rows.append(f"('{r['id_mahasiswa']}',{r['angkatan']},'{pred}',{prob})")
    spark.sql(f"INSERT INTO {ns}.gold.model_predictions VALUES {','.join(mp_rows)}")
    print(f"  Batch {start}-{min(start+batch_size, total)} done")

# Verify
count = spark.table(f"{ns}.gold.model_predictions").count()
print(f"\nFinal count: {count}")

# Show distribution
spark.sql(f"SELECT angkatan, prediksi, COUNT(*) as cnt FROM {ns}.gold.model_predictions GROUP BY angkatan, prediksi ORDER BY angkatan, prediksi").show(20, truncate=False)

spark.stop()
print("Done.")
