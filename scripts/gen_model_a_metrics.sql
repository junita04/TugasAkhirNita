DROP TABLE IF EXISTS iceberg.gold.model_metrics_model_a;
CREATE TABLE iceberg.gold.model_metrics_model_a (
  model varchar,
  cv_mean_accuracy double,
  cv_std_accuracy double,
  cv_mean_f1 double,
  cv_std_f1 double,
  test_accuracy double,
  test_precision double,
  test_recall double,
  test_f1 double,
  training_samples integer,
  test_samples integer,
  inference_samples integer,
  features_count integer,
  pipeline_version varchar,
  training_date varchar
);
INSERT INTO iceberg.gold.model_metrics_model_a VALUES (
  'model_a_utama',
  0.7297623534610486,
  0.01519875377313164,
  0.7324877666842833,
  NULL,
  0.727184779103515,
  0.7404502195011711,
  0.727184779103515,
  0.7316476836489404,
  12404,
  3101,
  12338,
  5,
  'model_a_utama',
  '2026-10-05T13:27:01'
);

DROP TABLE IF EXISTS iceberg.gold.confusion_matrix_model_a;
CREATE TABLE iceberg.gold.confusion_matrix_model_a (
  actual varchar,
  predicted varchar,
  count integer
);
INSERT INTO iceberg.gold.confusion_matrix_model_a VALUES
  ('Tepat Waktu', 'Tepat Waktu', 700),
  ('Tepat Waktu', 'Terlambat', 338),
  ('Terlambat', 'Tepat Waktu', 508),
  ('Terlambat', 'Terlambat', 1555);

DROP TABLE IF EXISTS iceberg.gold.classification_report_model_a;
CREATE TABLE iceberg.gold.classification_report_model_a (
  class varchar,
  precision double,
  recall double,
  f1_score double,
  support integer
);
INSERT INTO iceberg.gold.classification_report_model_a VALUES
  ('Tepat Waktu', 0.5794701986754967, 0.674373795761079, 0.6233303650934996, 1038),
  ('Terlambat', 0.8214474379292129, 0.7537566650508968, 0.7861476238624874, 2063),
  ('weighted_avg', 0.7404502195011711, 0.727184779103515, 0.7316476836489404, 3101);

SELECT * FROM iceberg.gold.model_metrics_model_a;
SELECT * FROM iceberg.gold.confusion_matrix_model_a;
SELECT * FROM iceberg.gold.classification_report_model_a;
