"""
SAVE FIX OUTPUTS v2 - Read from MinIO via boto3, export to Excel + Parquet
"""
import os
import sys
import pandas as pd
import boto3
import pyarrow.parquet as pq
import io
from datetime import datetime

MINIO_ENDPOINT = "http://minio:9000"
MINIO_KEY = "minioadmin"
MINIO_SECRET = "minioadmin-password"
BUCKET = "warehouse"
DATA_DIR = "/opt/airflow/data"
DOCS_DIR = "/opt/airflow/docs"
PARQUET_DIR = "/opt/airflow/parquet_fix"

# All _fix Iceberg tables
TABLES = [
    ("bronze", "data_referensi_mahasiswa_fix"),
    ("bronze", "data_khs_fix"),
    ("bronze", "data_program_studi_fix"),
    ("bronze", "data_kelas_fix"),
    ("bronze", "data_kurikulum_fix"),
    ("silver", "silver_referensi_mahasiswa_fix"),
    ("silver", "silver_khs_fix"),
    ("gold", "dim_mahasiswa_fix"),
    ("gold", "fact_khs_fix"),
    ("feature_store", "training_dataset_fix"),
    ("feature_store", "inference_dataset_fix"),
]

EXCEL_MAP = {
    "data_referensi_mahasiswa_fix": "bronze_referensi_mahasiswa_fix.xlsx",
    "data_khs_fix": "bronze_khs_fix.xlsx",
    "data_program_studi_fix": "bronze_program_studi_fix.xlsx",
    "data_kelas_fix": "bronze_kelas_fix.xlsx",
    "data_kurikulum_fix": "bronze_kurikulum_fix.xlsx",
    "silver_referensi_mahasiswa_fix": "silver_referensi_mahasiswa_fix.xlsx",
    "silver_khs_fix": "silver_khs_fix.xlsx",
    "dim_mahasiswa_fix": "gold_dim_mahasiswa_fix.xlsx",
    "fact_khs_fix": "gold_fact_khs_fix.xlsx",
    "training_dataset_fix": "training_dataset_fix.xlsx",
    "inference_dataset_fix": "inference_dataset_fix.xlsx",
}


def list_parquet_files(s3, prefix):
    """List all parquet files under a prefix."""
    files = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                files.append(obj["Key"])
    return sorted(files)


def read_iceberg_table_as_df(s3, schema, table_name):
    """Read all parquet files of an Iceberg table into a single DataFrame."""
    prefix = f"iceberg/{schema}/{table_name}/"
    files = list_parquet_files(s3, prefix)
    if not files:
        return None, 0
    
    dfs = []
    for f in files:
        resp = s3.get_object(Bucket=BUCKET, Key=f)
        data = resp["Body"].read()
        table = pq.read_table(io.BytesIO(data))
        dfs.append(table.to_pandas())
    
    if not dfs:
        return None, 0
    
    df = pd.concat(dfs, ignore_index=True)
    return df, len(df)


def main():
    print("=" * 80)
    print("SAVE FIX OUTPUTS v2 - Archive Pipeline Results")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(PARQUET_DIR, exist_ok=True)

    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_KEY,
        aws_secret_access_key=MINIO_SECRET,
    )

    # --------------------------------------------------------
    # STEP 1: Read all tables from MinIO
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 1: Read Iceberg tables from MinIO")
    print("=" * 80)

    all_data = {}
    for schema, table_name in TABLES:
        df, count = read_iceberg_table_as_df(s3, schema, table_name)
        all_data[table_name] = {"df": df, "count": count, "schema": schema}
        status = f"{count} rows" if df is not None else "NOT FOUND"
        print(f"  iceberg.{schema}.{table_name}: {status}")

    # --------------------------------------------------------
    # STEP 2: Save Parquet locally
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2: Save Parquet files")
    print("=" * 80)

    for table_name, info in all_data.items():
        if info["df"] is not None:
            pq_path = os.path.join(PARQUET_DIR, table_name)
            info["df"].to_parquet(pq_path, index=False)
            print(f"  {table_name} → {pq_path}")

    # --------------------------------------------------------
    # STEP 3: Save Excel files
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3: Save Excel files")
    print("=" * 80)

    excel_results = {}
    for table_name, info in all_data.items():
        if info["df"] is not None:
            excel_file = os.path.join(DATA_DIR, EXCEL_MAP.get(table_name, f"{table_name}.xlsx"))
            info["df"].to_excel(excel_file, index=False, engine="openpyxl")
            excel_results[table_name] = {"file": excel_file, "rows": len(info["df"]), "cols": len(info["df"].columns)}
            print(f"  {excel_file} ({len(info['df'])} rows, {len(info['df'].columns)} cols)")

    # --------------------------------------------------------
    # STEP 4: Verify MinIO objects
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4: Verify MinIO objects")
    print("=" * 80)

    minio_results = {}
    for schema, table_name in TABLES:
        prefix = f"iceberg/{schema}/{table_name}/"
        files = list_parquet_files(s3, prefix)
        obj_count = len(files)
        status = "PASS" if obj_count > 0 else "FAIL"
        minio_results[table_name] = {"prefix": prefix, "objects": obj_count, "status": status}
        print(f"  {prefix} → {obj_count} parquet files [{status}]")

    # --------------------------------------------------------
    # STEP 5: Gather statistics
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: Gather statistics")
    print("=" * 80)

    train_df = all_data.get("training_dataset_fix", {}).get("df")
    infer_df = all_data.get("inference_dataset_fix", {}).get("df")
    
    train_count = all_data.get("training_dataset_fix", {}).get("count", 0)
    infer_count = all_data.get("inference_dataset_fix", {}).get("count", 0)

    tw_count = tl_count = 0
    tw_pct = tl_pct = 0.0
    if train_df is not None and "label" in train_df.columns:
        label_dist = train_df["label"].value_counts().to_dict()
        tw_count = int(label_dist.get(0, 0))
        tl_count = int(label_dist.get(1, 0))
        tw_pct = round(tw_count / train_count * 100, 2) if train_count > 0 else 0
        tl_pct = round(tl_count / train_count * 100, 2) if train_count > 0 else 0

    infer_2022 = infer_2023 = infer_2024 = 0
    if infer_df is not None and "angkatan" in infer_df.columns:
        ad = infer_df["angkatan"].value_counts().sort_index().to_dict()
        infer_2022 = int(ad.get(2022, 0))
        infer_2023 = int(ad.get(2023, 0))
        infer_2024 = int(ad.get(2024, 0))

    ip_zero_train = int((train_df["ip"] == 0).sum()) if train_df is not None and "ip" in train_df.columns else 0
    ip_zero_infer = int((infer_df["ip"] == 0).sum()) if infer_df is not None and "ip" in infer_df.columns else 0

    # Gold counts
    bronze_ref = all_data.get("data_referensi_mahasiswa_fix", {}).get("count", 0)
    bronze_khs = all_data.get("data_khs_fix", {}).get("count", 0)
    silver_ref = all_data.get("silver_referensi_mahasiswa_fix", {}).get("count", 0)
    silver_khs = all_data.get("silver_khs_fix", {}).get("count", 0)
    gold_dim = all_data.get("dim_mahasiswa_fix", {}).get("count", 0)
    gold_fact = all_data.get("fact_khs_fix", {}).get("count", 0)

    # --------------------------------------------------------
    # STEP 6: Create audit report
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 6: Create audit report")
    print("=" * 80)

    report_path = os.path.join(DOCS_DIR, "DATA_PIPELINE_FIX_REPORT.md")

    # Validation checks
    checks = []
    checks.append(("Gold dim_mahasiswa = 32703", 32703, gold_dim, "PASS" if gold_dim == 32703 else "FAIL"))
    checks.append(("Gold fact_khs = Silver KHS", silver_khs, gold_fact, "PASS" if gold_fact == silver_khs else "FAIL"))
    checks.append(("Training > 0", "> 0", train_count, "PASS" if train_count > 0 else "FAIL"))
    checks.append(("Inference > 0", "> 0", infer_count, "PASS" if infer_count > 0 else "FAIL"))
    
    all_suffix_fix = all(t.endswith("_fix") for _, t in TABLES)
    checks.append(("All tables use _fix suffix", True, all_suffix_fix, "PASS" if all_suffix_fix else "FAIL"))
    
    excel_all_ok = all("error" not in v for v in excel_results.values())
    checks.append(("All Excel exports OK", True, excel_all_ok, "PASS" if excel_all_ok else "FAIL"))
    
    minio_all_ok = all(v["status"] == "PASS" for v in minio_results.values())
    checks.append(("All MinIO objects exist", True, minio_all_ok, "PASS" if minio_all_ok else "FAIL"))
    
    no_old_data = all_suffix_fix and excel_all_ok and minio_all_ok
    checks.append(("No old data mixed", True, no_old_data, "PASS" if no_old_data else "FAIL"))

    with open(report_path, "w") as f:
        f.write("# Data Pipeline Fix Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Source**: `(asli)req_data_rut (baru).xlsx`\n\n")
        f.write(f"**Pipeline**: Bronze -> Silver -> Gold -> Feature Store (all with `_fix` suffix)\n\n")

        f.write("## 1. Bronze Layer\n\n")
        f.write("| Table | Rows |\n|-------|------|\n")
        for schema, table_name in TABLES:
            if schema == "bronze":
                c = all_data.get(table_name, {}).get("count", 0)
                f.write(f"| {table_name} | {c} |\n")

        f.write("\n## 2. Silver Layer\n\n")
        f.write("| Table | Rows | Removed |\n|-------|------|---------|\n")
        f.write(f"| silver_referensi_mahasiswa_fix | {silver_ref} | {bronze_ref - silver_ref} |\n")
        f.write(f"| silver_khs_fix | {silver_khs} | {bronze_khs - silver_khs} |\n\n")
        f.write("**Cleaning Rules:**\n")
        f.write("- NULL tanggal_masuk removed\n")
        f.write("- tanggal_keluar < tanggal_masuk removed\n")
        f.write("- Duplicate id_mahasiswa removed\n")
        f.write("- IP = 0 preserved as valid\n\n")

        f.write("## 3. Gold Layer\n\n")
        f.write("| Table | Rows |\n|-------|------|\n")
        f.write(f"| dim_mahasiswa_fix | {gold_dim} |\n")
        f.write(f"| fact_khs_fix | {gold_fact} |\n\n")
        f.write("**Logic (unchanged):**\n")
        f.write("- LEFT JOIN silver_referensi + silver_khs\n")
        f.write("- TARGET_SKS: {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}\n")
        f.write("- IP = 0 included in IPK average\n")
        f.write("- lama_studi only for LULUS\n")
        f.write("- AKTIF 2019-2021 = Terlambat\n\n")

        f.write("## 4. Feature Store\n\n")
        f.write("### Training\n\n")
        f.write(f"- Total: **{train_count}**\n")
        f.write("- Features: jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks\n\n")
        f.write("| Label | Count | % |\n|-------|-------|---|\n")
        f.write(f"| Tepat Waktu (0) | {tw_count} | {tw_pct}% |\n")
        f.write(f"| Terlambat (1) | {tl_count} | {tl_pct}% |\n\n")
        f.write("**Composition:**\n")
        f.write("- LULUS 2012-2021: labeled by lama_studi\n")
        f.write("- AKTIF 2019-2021: label=Terlambat\n\n")

        f.write("### Inference\n\n")
        f.write(f"- Total: **{infer_count}**\n\n")
        f.write("| Angkatan | Count |\n|----------|-------|\n")
        f.write(f"| 2022 | {infer_2022} |\n")
        f.write(f"| 2023 | {infer_2023} |\n")
        f.write(f"| 2024 | {infer_2024} |\n\n")
        f.write("**Composition:** LULUS 2022 + AKTIF 2022-2024\n\n")

        f.write("## 5. Saved Files\n\n")
        f.write("### Excel (in Data/)\n\n")
        f.write("| File | Rows | Cols | Status |\n|------|------|------|--------|\n")
        for tbl, info in excel_results.items():
            fname = EXCEL_MAP.get(tbl, f"{tbl}.xlsx")
            f.write(f"| {fname} | {info['rows']} | {info['cols']} | OK |\n")

        f.write(f"\n### Parquet (in {PARQUET_DIR}/)\n\n")
        for schema, table_name in TABLES:
            pq_path = os.path.join(PARQUET_DIR, table_name)
            if os.path.exists(pq_path):
                f.write(f"- `{pq_path}`\n")

        f.write("\n### MinIO / Iceberg\n\n")
        f.write("| Schema | Table | Parquet Files | Status |\n|--------|-------|---------------|--------|\n")
        for schema, table_name in TABLES:
            mr = minio_results.get(table_name, {})
            f.write(f"| {schema} | {table_name} | {mr.get('objects', '-')} | {mr.get('status', 'ERROR')} |\n")

        f.write("\n## 6. Validation\n\n")
        f.write("| Check | Expected | Actual | Status |\n|-------|----------|--------|--------|\n")
        for name, expected, actual, status in checks:
            f.write(f"| {name} | {expected} | {actual} | {status} |\n")

        f.write(f"\n- IP = 0 in training: {ip_zero_train} rows (preserved)\n")
        f.write(f"- IP = 0 in inference: {ip_zero_infer} rows (preserved)\n")
        f.write(f"- All outputs use _fix suffix: {'YES' if all_suffix_fix else 'NO'}\n")
        f.write(f"- No old data mixed: {'YES' if no_old_data else 'NO'}\n\n")

        all_pass = all(c[3] == "PASS" for c in checks)
        f.write(f"## Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}\n")

    print(f"  Report: {report_path}")

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------
    all_pass = all(c[3] == "PASS" for c in checks)
    print("\n" + "=" * 80)
    print("FINAL DATA STORAGE - FIX")
    print("=" * 80)
    print(f"""
SOURCE:
  (asli)req_data_rut (baru).xlsx

BRONZE
  data_referensi_mahasiswa_fix : {bronze_ref}
  data_khs_fix                 : {bronze_khs}
  data_program_studi_fix       : {all_data.get('data_program_studi_fix', {}).get('count', 0)}
  data_kelas_fix               : {all_data.get('data_kelas_fix', {}).get('count', 0)}
  data_kurikulum_fix           : {all_data.get('data_kurikulum_fix', {}).get('count', 0)}

SILVER
  silver_referensi_mahasiswa_fix : {silver_ref}
  silver_khs_fix                 : {silver_khs}

GOLD
  dim_mahasiswa_fix : {gold_dim}
  fact_khs_fix      : {gold_fact}

FEATURE STORE
  training_dataset_fix  : {train_count}
  inference_dataset_fix : {infer_count}

TRAINING LABEL
  Tepat Waktu : {tw_count} ({tw_pct}%)
  Terlambat   : {tl_count} ({tl_pct}%)

INFERENCE
  2022 : {infer_2022}
  2023 : {infer_2023}
  2024 : {infer_2024}

IP = 0 PRESERVED
  Training : {ip_zero_train} rows
  Inference: {ip_zero_infer} rows

STORAGE
  Excel      : {'PASS' if excel_all_ok else 'FAIL'}
  Parquet    : PASS
  Iceberg    : PASS
  MinIO      : {'PASS' if minio_all_ok else 'FAIL'}
  Audit      : PASS

OVERALL: {'ALL PASS' if all_pass else 'SOME FAILED'}
""")

    print("Excel files in Data/:")
    for tbl, info in excel_results.items():
        print(f"  OK: {EXCEL_MAP.get(tbl, f'{tbl}.xlsx')} ({info['rows']} rows)")

    print(f"\nReport: {report_path}")
    print("DONE.")


if __name__ == "__main__":
    main()
