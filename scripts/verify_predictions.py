import pandas as pd

pred = pd.read_parquet('/opt/airflow/data/predictions/prediction_result_without_smote.parquet')
print(f'Total predictions: {len(pred)}')
print(f'Distinct IDs: {pred["id_mahasiswa"].nunique()}')
print(f'Angkatan distribution:')
print(pred['angkatan'].value_counts().sort_index())
print()
print('Prediction distribution:')
print(pred['prediksi_label'].value_counts())
print()
print('=== WITHOUT SMOTE - DISTRIBUTION BY ANGKATAN ===')
for a in [2022, 2023, 2024]:
    subset = pred[pred['angkatan'] == a]
    total = len(subset)
    tw = len(subset[subset['prediksi_label'] == 0])
    tl = len(subset[subset['prediksi_label'] == 1])
    print(f'Angkatan {a}: TW={tw} ({tw/total*100:.2f}%), TL={tl} ({tl/total*100:.2f}%), Total={total}')
