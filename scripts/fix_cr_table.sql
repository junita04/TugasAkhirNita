-- Drop and recreate classification_report_final with correct column name
DROP TABLE IF EXISTS iceberg.gold.classification_report_final;

CREATE TABLE iceberg.gold.classification_report_final (
    model STRING,
    class STRING,
    precision DOUBLE,
    recall DOUBLE,
    f1_score DOUBLE,
    support BIGINT
) USING iceberg;

-- Model A: 4_features
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_4_features', 'Tepat Waktu', 0.5185, 0.4897, 0.5037, 631);
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_4_features', 'Terlambat', 0.8422, 0.8569, 0.8495, 2006);
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_4_features', 'accuracy', 0.7691, 0.7691, 0.7691, 2637);

-- Model B: 8_features without SMOTE
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_8_features_without_smote', 'Tepat Waktu', 0.48, 0.65, 0.55, 631);
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_8_features_without_smote', 'Terlambat', 0.88, 0.78, 0.82, 2006);
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_8_features_without_smote', 'accuracy', 0.75, 0.75, 0.75, 2637);

-- Model B: 8_features with SMOTE
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_8_features_with_smote', 'Tepat Waktu', 0.42, 0.82, 0.56, 631);
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_8_features_with_smote', 'Terlambat', 0.92, 0.64, 0.76, 2006);
INSERT INTO iceberg.gold.classification_report_final VALUES ('GaussianNB_8_features_with_smote', 'accuracy', 0.69, 0.69, 0.69, 2637);
