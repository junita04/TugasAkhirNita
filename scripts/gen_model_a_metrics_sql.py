import json

META = r"D:\TA\TugasAkhirNita\models\model_a_utama_metadata.json"
OUT = r"D:\TA\TugasAkhirNita\scripts\gen_model_a_metrics.sql"

with open(META) as f:
    m = json.load(f)

h = m["holdout_metrics"]
cm = h["confusion_matrix"]
cv = m["cv_results"]["per_fold_summary"]

sup_tw = cm["tp_tepat"] + cm["fn_tepat"]
sup_tl = cm["fp_tepat"] + cm["tp_terlambat"]
n_test = sup_tw + sup_tl

tr_tw = 5191 - sup_tw
tr_tl = 10314 - sup_tl
n_train = tr_tw + tr_tl

w_prec = (h["precision_tepat_waktu"] * sup_tw + h["precision_terlambat"] * sup_tl) / n_test
w_rec = (h["recall_tepat_waktu"] * sup_tw + h["recall_terlambat"] * sup_tl) / n_test
w_f1 = (h["f1_tepat_waktu"] * sup_tw + h["f1_terlambat"] * sup_tl) / n_test

cv_f1 = (
    cv["F1 Tepat Waktu"]["mean"] * tr_tw + cv["F1 Terlambat"]["mean"] * tr_tl
) / n_train

assert abs(w_rec - h["accuracy"]) < 1e-9, (w_rec, h["accuracy"])

sql = f"""\
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
  {cv["Accuracy"]["mean"]!r},
  {cv["Accuracy"]["std"]!r},
  {cv_f1!r},
  NULL,
  {h["accuracy"]!r},
  {w_prec!r},
  {w_rec!r},
  {w_f1!r},
  {n_train},
  {n_test},
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
  ('Tepat Waktu', 'Tepat Waktu', {cm["tp_tepat"]}),
  ('Tepat Waktu', 'Terlambat', {cm["fn_tepat"]}),
  ('Terlambat', 'Tepat Waktu', {cm["fp_tepat"]}),
  ('Terlambat', 'Terlambat', {cm["tp_terlambat"]});

DROP TABLE IF EXISTS iceberg.gold.classification_report_model_a;
CREATE TABLE iceberg.gold.classification_report_model_a (
  class varchar,
  precision double,
  recall double,
  f1_score double,
  support integer
);
INSERT INTO iceberg.gold.classification_report_model_a VALUES
  ('Tepat Waktu', {h["precision_tepat_waktu"]!r}, {h["recall_tepat_waktu"]!r}, {h["f1_tepat_waktu"]!r}, {sup_tw}),
  ('Terlambat', {h["precision_terlambat"]!r}, {h["recall_terlambat"]!r}, {h["f1_terlambat"]!r}, {sup_tl}),
  ('weighted_avg', {w_prec!r}, {w_rec!r}, {w_f1!r}, {n_test});

SELECT * FROM iceberg.gold.model_metrics_model_a;
SELECT * FROM iceberg.gold.confusion_matrix_model_a;
SELECT * FROM iceberg.gold.classification_report_model_a;
"""

with open(OUT, "w") as f:
    f.write(sql)

print(f"supports: tw={sup_tw} tl={sup_tl} n_test={n_test}")
print(f"train: tw={tr_tw} tl={tr_tl} n_train={n_train}")
print(f"test_acc={h['accuracy']:.6f} w_prec={w_prec:.6f} w_rec={w_rec:.6f} w_f1={w_f1:.6f}")
print(f"cv_f1={cv_f1:.6f}")
print("written", OUT)
