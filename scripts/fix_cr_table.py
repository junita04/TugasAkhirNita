"""Recreate classification_report_final with correct schema."""
import sys
sys.path.insert(0, "/opt/airflow")
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

spark = get_spark("Fix Classification Report")
ns = ICEBERG_NAMESPACE

print("Dropping old table...")
spark.sql(f"DROP TABLE IF EXISTS {ns}.gold.classification_report_final")

print("Creating new table with correct schema...")
spark.sql(f"""
CREATE TABLE {ns}.gold.classification_report_final (
    model STRING,
    class STRING,
    precision DOUBLE,
    recall DOUBLE,
    f1_score DOUBLE,
    support BIGINT
) USING iceberg
""")

# Model A: 4_features
print("Inserting Model A (4_features)...")
for cls, p, r, f, s in [
    ("Tepat Waktu", 0.5185, 0.4897, 0.5037, 631),
    ("Terlambat", 0.8422, 0.8569, 0.8495, 2006),
    ("accuracy", 0.7691, 0.7691, 0.7691, 2637),
]:
    spark.sql(f"INSERT INTO {ns}.gold.classification_report_final VALUES ('GaussianNB_4_features', '{cls}', {p}, {r}, {f}, {s})")

# Model B: 8_features without SMOTE
print("Inserting Model B (8_features_without_smote)...")
for cls, p, r, f, s in [
    ("Tepat Waktu", 0.48, 0.65, 0.55, 631),
    ("Terlambat", 0.88, 0.78, 0.82, 2006),
    ("accuracy", 0.75, 0.75, 0.75, 2637),
]:
    spark.sql(f"INSERT INTO {ns}.gold.classification_report_final VALUES ('GaussianNB_8_features_without_smote', '{cls}', {p}, {r}, {f}, {s})")

# Model B: 8_features with SMOTE
print("Inserting Model B (8_features_with_smote)...")
for cls, p, r, f, s in [
    ("Tepat Waktu", 0.42, 0.82, 0.56, 631),
    ("Terlambat", 0.92, 0.64, 0.76, 2006),
    ("accuracy", 0.69, 0.69, 0.69, 2637),
]:
    spark.sql(f"INSERT INTO {ns}.gold.classification_report_final VALUES ('GaussianNB_8_features_with_smote', '{cls}', {p}, {r}, {f}, {s})")

print("Done! Verifying...")
result = spark.sql(f"SELECT * FROM {ns}.gold.classification_report_final ORDER BY model, class")
result.show(20, truncate=False)

spark.stop()
