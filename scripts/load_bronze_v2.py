import sys
sys.path.insert(0, '/opt/airflow')

import pandas as pd
import numpy as np
from pathlib import Path

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

EXCEL_PATH = Path('/opt/airflow/data/req_data_rut_baruu.xlsx')
TEMP_DIR = Path('/opt/airflow/data/temp_bronze')
TEMP_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("BRONZE LAYER - PANDAS + PARQUET APPROACH")
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

# Step 1: Read all sheets with pandas and save as parquet
print()
print("STEP 1: Reading Excel with pandas...")
for sheet in xl.sheet_names:
    table_name = EXPECTED_SHEETS_TO_TABLE.get(sheet, sheet.lower().replace(" ", "_"))
    print(f"  {sheet} -> {table_name}")
    
    df_pd = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
    
    if df_pd.empty or len(df_pd.columns) == 0:
        print(f"    SKIP: Empty")
        continue
    
    print(f"    Rows: {len(df_pd)}, Cols: {len(df_pd.columns)}")
    
    # Save as parquet
    parquet_path = TEMP_DIR / f"{table_name}.parquet"
    df_pd.to_parquet(parquet_path, index=False)
    print(f"    Saved: {parquet_path}")

# Step 2: Load parquet files into Spark and write to Iceberg
print()
print("STEP 2: Loading parquet into Iceberg Bronze...")

spark = get_spark("Bronze - Parquet Load")

success_tables = []
skipped_sheets = []
failed_sheets = []

for sheet in xl.sheet_names:
    table_name = EXPECTED_SHEETS_TO_TABLE.get(sheet, sheet.lower().replace(" ", "_"))
    parquet_path = TEMP_DIR / f"{table_name}.parquet"
    
    if not parquet_path.exists():
        print(f"  {table_name}: SKIP (no parquet)")
        skipped_sheets.append(sheet)
        continue
    
    try:
        print(f"  {table_name}: Loading...")
        
        df_spark = spark.read.parquet(str(parquet_path))
        df_spark = df_spark.coalesce(1)
        
        full_table = f"{ICEBERG_NAMESPACE}.bronze.{table_name}"
        spark.sql(f"DROP TABLE IF EXISTS {full_table}")
        df_spark.write.format("iceberg").mode("overwrite").saveAsTable(full_table)
        
        count = spark.table(full_table).count()
        print(f"    OK: {count} rows -> {full_table}")
        success_tables.append(table_name)
        
    except Exception as e:
        print(f"    FAIL: {e}")
        failed_sheets.append(sheet)

spark.stop()

print()
print("=" * 60)
print("BRONZE LOADING SUMMARY")
print("=" * 60)
print(f"Success: {success_tables}")
print(f"Skipped: {skipped_sheets}")
print(f"Failed: {failed_sheets}")
