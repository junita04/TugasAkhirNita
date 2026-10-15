import pandas as pd
df = pd.read_excel('/opt/airflow/Data/data fix/training_dataset_full.xlsx')
print('TRAINING:')
print('Shape:', df.shape)
print('Columns:', list(df.columns))
print()
print(df.dtypes)
print()
print(df.head(3).to_string())