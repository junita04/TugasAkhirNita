import sys, os
sys.path.insert(0, '/opt/airflow')
os.environ['SPARK_EVENT_LOG'] = 'false'

from backend.spark.session import get_spark
spark = get_spark('Metadata-Update')

old_prefix = 'file:///D:/TA/TugasAkhirNita/iceberg'
new_prefix = 's3a://warehouse/iceberg'

schemas = {
    'bronze': ['data_referensi_mahasiswa', 'data_kelas', 'data_khs', 'data_kurikulum', 'data_program_studi'],
    'silver': ['data_referensi_mahasiswa', 'data_kelas', 'data_khs', 'data_kurikulum', 'data_program_studi',
               'silver_mahasiswa', 'silver_kelas', 'silver_khs', 'silver_kurikulum', 'silver_program_studi'],
    'gold': ['dim_mahasiswa', 'fact_khs', 'gold_kurikulum', 'gold_mahasiswa', 'gold_mahasiswa_fakta', 'gold_program_studi'],
    'feature_store': ['training_dataset', 'inference_dataset', 'prediction_result',
                      'prediction_result_with_smote', 'prediction_result_without_smote', 'prediction_comparison']
}

for schema, tables in schemas.items():
    for t in tables:
        try:
            full_name = 'iceberg.{}.{}'.format(schema, t)
            tbl = spark._jsparkSession.catalog().getTable('iceberg', '{}.{}'.format(schema, t))
            current_loc = tbl.location()
            if current_loc.startswith(old_prefix):
                new_loc = current_loc.replace(old_prefix, new_prefix, 1)
                sql = "ALTER TABLE {} SET LOCATION '{}'".format(full_name, new_loc)
                spark.sql(sql)
                print('OK {}.{}'.format(schema, t))
            else:
                print('SKIP {}.{}'.format(schema, t))
        except Exception as e:
            err = str(e)[:120]
            print('ERR {}.{}: {}'.format(schema, t, err))

spark.stop()
print('METADATA_UPDATE_DONE')
