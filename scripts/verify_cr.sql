SELECT model, class, precision, recall, f1_score, support
FROM gold.classification_report_final
ORDER BY model, class;
