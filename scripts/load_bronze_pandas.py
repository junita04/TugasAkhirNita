import sys
sys.path.insert(0, '/opt/airflow')

import pandas as pd
import numpy as np
from pathlib import Path

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

EXCEL_PATH = Path('/opt/airflow/data/req_data_rut_baruu.xlsx')

print("=" * 80)
print("BRONZE LAYER - PANDAS-BASED LOADING (AVOID OOM)")
print("=" * 80)

EXPECTED_SHEETS_TO_TABLE = {
    "Referensi Data Mahasiswa": "data_referensi_mahasiswa",
    "Data KHS": "data_khs",
    "Data Program Studi": "data_program_studi",
    "Data Mata Kuliah": "data_mata_kuliah",
    "Data Kelas": "data_kelas",
    "Data Kurikulum": "data_kurikulum",
}

xl = pd.ExcelFile(EXCEL_PATH)
print(f"Sheets: {xl.sheet_names}")

success_tables = []
skipped_sheets = []
failed_sheets = []

for sheet in xl.sheet_names:
    print(f"\n--- Processing: {sheet} ---")
    
    try:
        df_pd = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
        
        if df_pd.empty or len(df_pd.columns) == 0:
            print(f"  SKIP: Empty sheet")
            skipped_sheets.append(sheet)
            continue
        
        table_name = EXPECTED_SHEETS_TO_TABLE.get(sheet, sheet.lower().replace(" ", "_"))
        print(f"  Rows: {len(df_pd)}, Cols: {len(df_pd.columns)}")
        print(f"  Columns: {list(df_pd.columns)}")
        
        # Convert to Spark DataFrame
        spark = get_spark(f"Bronze - {sheet}")
        
        # Handle NaN for PySpark (convert NaN to None for object columns)
        for col in df_pd.columns:
            if df_pd[col].dtype == 'object':
                df_pd[col] = df_pd[col].where(df_pd[col].notna(), None)
        
        df_spark = spark.createDataFrame(df_pd)
        df_spark = df_spark.coalesce(1)
        
        full_table = f"{ICEBERG_NAMESPACE}.bronze.{table_name}"
        spark.sql(f"DROP TABLE IF EXISTS {full_table}")
        df_spark.write.format("iceberg").mode("overwrite").saveAsTable(full_table)
        
        count = spark.table(full_table).count()
        print(f"  OK: {table_name} ({count} rows)")
        success_tables.append(table_name)
        
        spark.stop()
        
    except Exception as e:
        print(f"  FAIL: {e}")
        failed_sheets.append(sheet)
        try:
            spark.stop()
        except:
            pass

print()
print("=" * 60)
print("BRONZE LOADING SUMMARY")
print("=" * 60)
print(f"Success: {success_tables}")
print(f"Skipped: {skipped_sheets}")
print(f"Failed: {failed_sheets}")
