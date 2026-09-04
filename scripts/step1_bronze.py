import sys
sys.path.insert(0, '/opt/airflow')
import pandas as pd
from pathlib import Path
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

EXCEL = Path('/opt/airflow/data/req_data_rut_baru.xlsx')
TEMP = Path('/opt/airflow/data/temp_bronze')
TEMP.mkdir(parents=True, exist_ok=True)

MAP = {
    "Referensi Data Mahasiswa": "data_referensi_mahasiswa",
    "Data KHS": "data_khs",
    "Data Program Studi": "data_program_studi",
    "Data Mata Kuliah": "data_mata_kuliah",
    "Data Kelas": "data_kelas",
    "Data Kurikulum": "data_kurikulum",
}

print("=" * 80)
print("BRONZE LAYER - LOAD FROM EXCEL")
print("=" * 80)

xl = pd.ExcelFile(EXCEL)
results = {}

for sheet in xl.sheet_names:
    df = pd.read_excel(EXCEL, sheet_name=sheet)
    tname = MAP.get(sheet, sheet.lower().replace(" ", "_"))
    if df.empty or len(df.columns) == 0:
        print(f"  SKIP: {sheet}")
        continue
    p = TEMP / f"{tname}.parquet"
    df.to_parquet(p, index=False)
    results[tname] = len(df)
    print(f"  {tname}: {len(df)} rows -> parquet")

print()
print("Loading parquet -> Iceberg Bronze...")
spark = get_spark("Bronze Load")
for tname, count in results.items():
    p = TEMP / f"{tname}.parquet"
    df = spark.read.parquet(str(p)).coalesce(1)
    full = f"{ICEBERG_NAMESPACE}.bronze.{tname}"
    spark.sql(f"DROP TABLE IF EXISTS {full}")
    df.write.format("iceberg").mode("overwrite").saveAsTable(full)
    actual = spark.table(full).count()
    print(f"  {tname}: {actual} rows -> {full}")
spark.stop()

print()
print("BRONZE COMPLETE")
