import sys
sys.path.insert(0, '/opt/airflow')
from backend.spark.session import get_spark

spark = get_spark('CheckTrainingByAngkatanDetailed')

# Check training dataset by angkatan and label
df = spark.table('iceberg.feature_store.training_dataset')

print('='*80)
print('LAKEHOUSE TRAINING DATASET BY ANGKATAN (DETAILED)')
print('='*80)

# Group by angkatan and label
result = df.groupBy('angkatan', 'label').count().orderBy('angkatan', 'label').collect()

# Print as table
print(f"{'Angkatan':<10} {'Label':<10} {'Count':>10}")
print('-' * 30)
for row in result:
    label_text = 'Tepat Waktu' if row['label'] == 0 else 'Terlambat'
    print(f"{row['angkatan']:<10} {label_text:<10} {row['count']:>10}")

# Calculate totals
print()
print('='*80)
print('SUMMARY')
print('='*80)

# Tepat Waktu (label=0)
tw = df.filter(df['label'] == 0).count()
tl = df.filter(df['label'] == 1).count()
print(f'Tepat Waktu (0): {tw}')
print(f'Terlambat (1)  : {tl}')
print(f'Total          : {tw + tl}')

# Check AKTIF 2019-2021
print()
print('AKTIF 2019-2021 in training:')
aktif_2019_2021 = df.filter(
    (df['angkatan'].isin(2019, 2020, 2021)) & 
    (df['label'] == 1)
)
print(f'  Count: {aktif_2019_2021.count()}')

spark.stop()
