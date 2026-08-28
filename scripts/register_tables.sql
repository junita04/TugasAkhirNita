-- Register Iceberg tables in HMS so Trino can see them
CALL iceberg.system.register_table('gold', 'model_metrics_final', 's3a://warehouse/iceberg/gold/model_metrics_final');
CALL iceberg.system.register_table('gold', 'confusion_matrix_final', 's3a://warehouse/iceberg/gold/confusion_matrix_final');
CALL iceberg.system.register_table('gold', 'classification_report_final', 's3a://warehouse/iceberg/gold/classification_report_final');
CALL iceberg.system.register_table('gold', 'prediction_by_angkatan_final', 's3a://warehouse/iceberg/gold/prediction_by_angkatan_final');
