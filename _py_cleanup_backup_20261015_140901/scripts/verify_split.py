import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_excel("/opt/airflow/Data/data fix/training_dataset_full.xlsx")
print(f"Total data: {len(df)}")
print(f"Label dist:\n{df['label'].value_counts().sort_index()}")
print(f"Label %:\n{(df['label'].value_counts(normalize=True).sort_index() * 100).round(2)}")

# Exact split as per reference
X = df[["angkatan_enc", "jk_enc", "ipk_kategori", "total_sks", "jumlah_mk"]]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"\nTraining: {len(X_train)}")
print(f"Testing: {len(X_test)}")
print(f"\nTraining label dist:\n{y_train.value_counts().sort_index()}")
print(f"Testing label dist:\n{y_test.value_counts().sort_index()}")

# Verify exact numbers
print(f"\n=== VERIFICATION ===")
print(f"Training label 0: {(y_train==0).sum()} (expected 4153)")
print(f"Training label 1: {(y_train==1).sum()} (expected 8251)")
print(f"Testing label 0:  {(y_test==0).sum()} (expected 1038)")
print(f"Testing label 1:  {(y_test==1).sum()} (expected 2063)")