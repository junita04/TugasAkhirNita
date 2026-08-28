CALL iceberg.system.unregister_table('gold', 'classification_report_final');
CALL iceberg.system.register_table('gold', 'classification_report_final', 's3a://warehouse/iceberg/gold/classification_report_final');
