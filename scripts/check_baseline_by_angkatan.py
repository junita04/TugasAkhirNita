import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd

# Read baseline training dataset
train_path = '/opt/airflow/data/model_8_features/training_dataset_8_features.xlsx'
train_df = pd.read_excel(train_path)

print('='*80)
print('BASELINE TRAINING DATASET BY ANGKATAN')
print('='*80)

# Check if angkatan column exists
if 'angkatan' in train_df.columns:
    # Group by angkatan and status_kelulusan
    result = train_df.groupby(['angkatan', 'status_kelulusan']).size().reset_index(name='count')
    print(result.to_string(index=False))
else:
    print('No angkatan column found')
    print('Columns:', train_df.columns.tolist())

print()
print('='*80)
print('SUMMARY')
print('='*80)
print(f'Total rows: {len(train_df)}')
tw = (train_df['status_kelulusan'] == 'Tepat Waktu').sum()
tl = (train_df['status_kelulusan'] == 'Terlambat').sum()
print(f'Tepat Waktu: {tw}')
print(f'Terlambat: {tl}')
print(f'Total: {tw + tl}')
