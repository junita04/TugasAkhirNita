import pandas as pd

# Check prediction results
pred_without = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_without_smote.parquet')
pred_with = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_with_smote.parquet')

print('=== PREDICTION RESULTS ===')
print(f'Without SMOTE: {len(pred_without)} rows')
print(f'With SMOTE: {len(pred_with)} rows')

print()
print('=== WITHOUT SMOTE - sks_seharusnya stats ===')
print(pred_without['sks_seharusnya'].describe())

print()
print('=== WITHOUT SMOTE - DISTRIBUTION BY ANGKATAN ===')
for a in [2022, 2023, 2024]:
    subset = pred_without[pred_without['angkatan'] == a]
    total = len(subset)
    tw = len(subset[subset['prediksi_label'] == 0])
    tl = len(subset[subset['prediksi_label'] == 1])
    sks = subset['sks_seharusnya'].iloc[0]
    sem = subset['angkatan'].iloc[0]
    print(f'Angkatan {a}: TW={tw} ({tw/total*100:.2f}%), TL={tl} ({tl/total*100:.2f}%), Total={total}, sks_seharusnya={sks}')

print()
print('=== VALIDATION ===')
print(f'sks_seharusnya min: {pred_without["sks_seharusnya"].min()}')
print(f'sks_seharusnya max: {pred_without["sks_seharusnya"].max()}')
print(f'No values > 144: {(pred_without["sks_seharusnya"] > 144).sum() == 0}')
print(f'No values < 15: {(pred_without["sks_seharusnya"] < 15).sum() == 0}')

print()
print('=== ANGKATAN 2022 VALIDATION ===')
a2022 = pred_without[pred_without['angkatan'] == 2022]
print(f'Expected: semester=7, sks_seharusnya=135')
print(f'Actual: sks_seharusnya={a2022["sks_seharusnya"].iloc[0]}')

print()
print('=== ANGKATAN 2023 VALIDATION ===')
a2023 = pred_without[pred_without['angkatan'] == 2023]
print(f'Expected: semester=5, sks_seharusnya=95')
print(f'Actual: sks_seharusnya={a2023["sks_seharusnya"].iloc[0]}')

print()
print('=== ANGKATAN 2024 VALIDATION ===')
a2024 = pred_without[pred_without['angkatan'] == 2024]
print(f'Expected: semester=3, sks_seharusnya=55')
print(f'Actual: sks_seharusnya={a2024["sks_seharusnya"].iloc[0]}')
