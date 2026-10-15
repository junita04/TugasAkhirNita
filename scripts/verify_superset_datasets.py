"""Verifikasi 26 dataset Superset terhadap Trino: fisik count(*), virtual SQL asli."""

import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, r"D:\TA\TugasAkhirNita\scripts")
from restore_iceberg_all import TrinoError, trino_execute, qident  # noqa: E402

SUPSET_SQL = {
    18: (
        "SELECT COUNT(*) FROM (SELECT CASE "
        "WHEN ipk < 2.00 THEN '1. < 2.00' "
        "WHEN ipk >= 2.00 AND ipk < 2.50 THEN '2. 2.00-2.49' "
        "WHEN ipk >= 2.50 AND ipk < 3.00 THEN '3. 2.50-2.99' "
        "WHEN ipk >= 3.00 AND ipk < 3.50 THEN '4. 3.00-3.49' "
        "WHEN ipk >= 3.50 AND ipk <= 4.00 THEN '5. 3.50-4.00' "
        "ELSE '6. Tidak Valid' END AS rentang_ipk, COUNT(*) AS jumlah_mahasiswa "
        "FROM iceberg.gold.data_referensi_mahasiswa "
        "WHERE status_mahasiswa = 'AKTIF' AND ipk IS NOT NULL AND ipk BETWEEN 0 AND 4 "
        "GROUP BY 1) t"
    ),
    40: (
        "SELECT COUNT(*) FROM (SELECT 'Total Mahasiswa' AS label, CAST(COUNT(*) AS VARCHAR) AS value "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Mahasiswa Aktif', CAST(COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Mahasiswa Lulus', CAST(COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Mahasiswa Tepat Waktu', CAST(COUNT(CASE WHEN label=0 THEN 1 END) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Mahasiswa Terlambat', CAST(COUNT(CASE WHEN label=1 THEN 1 END) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Rata-rata IPK', CAST(CAST(ROUND(CAST(AVG(ipk) AS DOUBLE), 2) AS DECIMAL(10,2)) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Rata-rata IP', CAST(CAST(ROUND(CAST(AVG(ip) AS DOUBLE), 2) AS DECIMAL(10,2)) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa "
        "UNION ALL SELECT 'Rata-rata Total SKS', CAST(CAST(ROUND(CAST(AVG(total_sks) AS DOUBLE), 1) AS DECIMAL(10,1)) AS VARCHAR) "
        "FROM iceberg.gold.dim_mahasiswa) t"
    ),
}

DATASETS = [
    (5, "gold", "data_referensi_mahasiswa"),
    (6, "gold", "model_metrics_final"),
    (7, "gold", "model_predictions"),
    (8, "gold", "prediction_by_angkatan_final"),
    (9, "gold", "confusion_matrix_final"),
    (10, "gold", "classification_report_final"),
    (18, "gold", "ipk_dist_view"),
    (19, "gold", "gold_mahasiswa"),
    (20, "gold", "gold_program_studi"),
    (21, "gold", "gold_kurikulum"),
    (22, "feature_store", "prediction_result"),
    (27, "gold", "dim_mahasiswa"),
    (28, "gold", "fact_khs"),
    (29, "feature_store", "training_dataset"),
    (30, "feature_store", "inference_dataset"),
    (31, "feature_store", "prediction_result_without_smote"),
    (32, "feature_store", "prediction_result_with_smote"),
    (33, "feature_store", "prediction_comparison"),
    (34, "gold", "dim_mahasiswa_fix"),
    (35, "gold", "fact_khs_fix"),
    (36, "gold", "model_predictions_v2"),
    (37, "gold", "prediction_by_angkatan_v2"),
    (38, "feature_store", "training_dataset_v2"),
    (39, "feature_store", "inference_dataset_v2"),
    (40, "gold", "kpi_summary"),
    (41, "feature_store", "inference_result"),
]

ok, fail = [], []
for ds_id, schema, table in DATASETS:
    if ds_id in SUPSET_SQL:
        sql = SUPSET_SQL[ds_id]
    else:
        sql = f"SELECT count(*) FROM iceberg.{qident(schema)}.{qident(table)}"
    try:
        rows = trino_execute(sql)
        n = rows[0][0] if rows and rows[0] else None
        ok.append((ds_id, f"{schema}.{table}", n))
        print(f"OK   ds={ds_id:<3} {schema}.{table:<40} rows={n}")
    except TrinoError as e:
        fail.append((ds_id, f"{schema}.{table}", str(e)))
        print(f"FAIL ds={ds_id:<3} {schema}.{table:<40} {e}")

print(f"\nverified={len(ok)} failed={len(fail)}")
with open(r"D:\TA\TugasAkhirNita\scripts\superset_dataset_check.json", "w", encoding="utf-8") as f:
    json.dump({"ok": ok, "failed": fail}, f, indent=2, ensure_ascii=False)
sys.exit(1 if fail else 0)
