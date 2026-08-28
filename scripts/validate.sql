-- Verify gold results tables via Trino
SELECT 'model_metrics_final' as tbl, count(*) as rows FROM gold.model_metrics_final
UNION ALL
SELECT 'confusion_matrix_final', count(*) FROM gold.confusion_matrix_final
UNION ALL
SELECT 'classification_report_final', count(*) FROM gold.classification_report_final
UNION ALL
SELECT 'prediction_by_angkatan_final', count(*) FROM gold.prediction_by_angkatan_final
