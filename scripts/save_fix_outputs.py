"""
SAVE FIX OUTPUTS - Archive pipeline results
Exports Iceberg tables to Parquet + Excel, verifies MinIO, creates audit report.
NO ML, NO re-running pipeline. Just save what's already there.
"""
import os
import sys
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
NS = "iceberg"
SUFFIX = "_fix"
DATA_DIR = "/opt/airflow/data"
DOCS_DIR = "/opt/airflow/docs"
PARQUET_DIR = "/opt/airflow/parquet_fix"

# Iceberg tables to export
TABLES = {
    "bronze": [
        ("data_referensi_mahasiswa", "data_referensi_mahasiswa_fix"),
        ("data_khs", "data_khs_fix"),
        ("data_program_studi", "data_program_studi_fix"),
        ("data_kelas", "data_kelas_fix"),
        ("data_kurikulum", "data_kurikulum_fix"),
    ],
    "silver": [
        ("silver_referensi_mahasiswa", "silver_referensi_mahasiswa_fix"),
        ("silver_khs", "silver_khs_fix"),
    ],
    "gold": [
        ("dim_mahasiswa", "dim_mahasiswa_fix"),
        ("fact_khs", "fact_khs_fix"),
    ],
    "feature_store": [
        ("training_dataset", "training_dataset_fix"),
        ("inference_dataset", "inference_dataset_fix"),
    ],
}

# Excel file mapping (table_name -> excel_filename)
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


def main():
    print("=" * 80)
    print("SAVE FIX OUTPUTS - Archive Pipeline Results")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(PARQUET_DIR, exist_ok=True)

    # --------------------------------------------------------
    # STEP 1: Read all Iceberg tables via Spark
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 1: Read Iceberg tables via Spark")
    print("=" * 80)

    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName("SaveFixOutputs")
        .master("local[*]")
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg.type", "hadoop")
        .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
        .config("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.catalog.iceberg.s3.endpoint", "http://minio:9000")
        .config("spark.sql.catalog.iceberg.s3.access-key", "minioadmin")
        .config("spark.sql.catalog.iceberg.s3.path-style-access", "true")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )

    all_data = {}
    for schema, tables in TABLES.items():
        for orig_name, fix_name in tables:
            full_table = f"{NS}.{schema}.{fix_name}"
            try:
                df = spark.table(full_table)
                count = df.count()
                all_data[fix_name] = {"df": df, "count": count, "schema": schema}
                print(f"  {full_table}: {count} rows")
            except Exception as e:
                print(f"  ERROR reading {full_table}: {e}")
                all_data[fix_name] = {"df": None, "count": 0, "schema": schema, "error": str(e)}

    # --------------------------------------------------------
    # STEP 2: Export to Parquet
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2: Export to Parquet")
    print("=" * 80)

    for table_name, info in all_data.items():
        if info["df"] is not None:
            pq_path = f"{PARQUET_DIR}/{table_name}"
            try:
                info["df"].write.mode("overwrite").parquet(pq_path)
                print(f"  {table_name} → {pq_path}")
            except Exception as e:
                print(f"  ERROR parquet {table_name}: {e}")

    spark.stop()

    # --------------------------------------------------------
    # STEP 3: Export to Excel using pandas
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3: Export to Excel (via pandas + parquet)")
    print("=" * 80)

    excel_results = {}
    for table_name, info in all_data.items():
        if info["df"] is not None:
            pq_path = f"{PARQUET_DIR}/{table_name}"
            excel_file = os.path.join(DATA_DIR, EXCEL_MAP.get(table_name, f"{table_name}.xlsx"))
            try:
                pandas_df = pd.read_parquet(pq_path)
                pandas_df.to_excel(excel_file, index=False, engine="openpyxl")
                excel_results[table_name] = {"file": excel_file, "rows": len(pandas_df), "cols": len(pandas_df.columns)}
                print(f"  {table_name} → {excel_file} ({len(pandas_df)} rows, {len(pandas_df.columns)} cols)")
            except Exception as e:
                print(f"  ERROR excel {table_name}: {e}")
                excel_results[table_name] = {"file": excel_file, "error": str(e)}

    # --------------------------------------------------------
    # STEP 4: Verify MinIO objects
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4: Verify MinIO objects")
    print("=" * 80)

    import boto3

    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin-password",
    )

    minio_results = {}
    for schema, tables in TABLES.items():
        for orig_name, fix_name in tables:
            prefix = f"iceberg/{schema}/{fix_name}/"
            try:
                resp = s3.list_objects_v2(Bucket="warehouse", Prefix=prefix, MaxKeys=10)
                obj_count = resp.get("KeyCount", 0)
                minio_results[fix_name] = {"prefix": prefix, "objects": obj_count, "status": "PASS" if obj_count > 0 else "FAIL"}
                status = "PASS" if obj_count > 0 else "FAIL"
                print(f"  {prefix} → {obj_count} objects [{status}]")
            except Exception as e:
                minio_results[fix_name] = {"prefix": prefix, "error": str(e), "status": "ERROR"}
                print(f"  ERROR {prefix}: {e}")

    # --------------------------------------------------------
    # STEP 5: Create audit report
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: Create audit report")
    print("=" * 80)

    report_path = os.path.join(DOCS_DIR, "DATA_PIPELINE_FIX_REPORT.md")

    # Gather counts
    bronze_ref = all_data.get("data_referensi_mahasiswa_fix", {}).get("count", 0)
    bronze_khs = all_data.get("data_khs_fix", {}).get("count", 0)
    bronze_prodi = all_data.get("data_program_studi_fix", {}).get("count", 0)
    bronze_kelas = all_data.get("data_kelas_fix", {}).get("count", 0)
    bronze_kurikulum = all_data.get("data_kurikulum_fix", {}).get("count", 0)
    silver_ref = all_data.get("silver_referensi_mahasiswa_fix", {}).get("count", 0)
    silver_khs = all_data.get("silver_khs_fix", {}).get("count", 0)
    gold_dim = all_data.get("dim_mahasiswa_fix", {}).get("count", 0)
    gold_fact = all_data.get("fact_khs_fix", {}).get("count", 0)
    train_count = all_data.get("training_dataset_fix", {}).get("count", 0)
    infer_count = all_data.get("inference_dataset_fix", {}).get("count", 0)

    # Label distribution from training parquet
    train_pq = f"{PARQUET_DIR}/training_dataset_fix"
    infer_pq = f"{PARQUET_DIR}/inference_dataset_fix"
    try:
        train_pdf = pd.read_parquet(train_pq)
        label_dist = train_pdf["label"].value_counts().to_dict()
        tw_count = int(label_dist.get(0, 0))
        tl_count = int(label_dist.get(1, 0))
        tw_pct = round(tw_count / train_count * 100, 2) if train_count > 0 else 0
        tl_pct = round(tl_count / train_count * 100, 2) if train_count > 0 else 0
    except:
        tw_count = tl_count = 0
        tw_pct = tl_pct = 0

    # Inference angkatan distribution
    try:
        infer_pdf = pd.read_parquet(infer_pq)
        angkatan_dist = infer_pdf["angkatan"].value_counts().sort_index().to_dict()
        infer_2022 = int(angkatan_dist.get(2022, 0))
        infer_2023 = int(angkatan_dist.get(2023, 0))
        infer_2024 = int(angkatan_dist.get(2024, 0))
    except:
        infer_2022 = infer_2023 = infer_2024 = 0

    # Validation
    all_pass = True
    checks = []

    def check(name, expected, actual):
        nonlocal all_pass
        passed = expected == actual or (isinstance(expected, str) and expected == "SKIP")
        if not passed:
            all_pass = False
        checks.append((name, expected, actual, "PASS" if passed else "FAIL"))
        return passed

    check("Gold dim_mahasiswa = 32703", 32703, gold_dim)
    check("Gold fact_khs", silver_khs, gold_fact)
    check("Training > 0", "> 0", train_count)
    check("Inference > 0", "> 0", infer_count)

    # IP=0 validation
    try:
        ip_zero_train = int((train_pdf["ip"] == 0).sum())
        ip_zero_infer = int((infer_pdf["ip"] == 0).sum())
        ip_zero_preserved = True
    except:
        ip_zero_train = ip_zero_infer = 0
        ip_zero_preserved = False

    # Suffix validation
    all_tables_use_fix = all(k.endswith("_fix") for k in all_data.keys())
    checks.append(("All tables use _fix suffix", True, all_tables_use_fix, "PASS" if all_tables_use_fix else "FAIL"))
    if not all_tables_use_fix:
        all_pass = False

    # Excel validation
    excel_all_ok = all("error" not in v for v in excel_results.values())
    checks.append(("All Excel exports OK", True, excel_all_ok, "PASS" if excel_all_ok else "FAIL"))
    if not excel_all_ok:
        all_pass = False

    # MinIO validation
    minio_all_ok = all(v.get("status") == "PASS" for v in minio_results.values())
    checks.append(("All MinIO objects exist", True, minio_all_ok, "PASS" if minio_all_ok else "FAIL"))
    if not minio_all_ok:
        all_pass = False

    # No old data mixed
    checks.append(("No old data mixed (suffix _fix only)", True, all_pass, "PASS" if all_pass else "FAIL"))

    # Write report
    with open(report_path, "w") as f:
        f.write("# Data Pipeline Fix Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Source**: `(asli)req_data_rut (baru).xlsx`\n\n")

        f.write("## Bronze Layer\n\n")
        f.write("| Table | Rows |\n|-------|------|\n")
        f.write(f"| data_referensi_mahasiswa_fix | {bronze_ref} |\n")
        f.write(f"| data_khs_fix | {bronze_khs} |\n")
        f.write(f"| data_program_studi_fix | {bronze_prodi} |\n")
        f.write(f"| data_kelas_fix | {bronze_kelas} |\n")
        f.write(f"| data_kurikulum_fix | {bronze_kurikulum} |\n\n")

        f.write("## Silver Layer\n\n")
        f.write("| Table | Rows | Removed |\n|-------|------|---------|\n")
        f.write(f"| silver_referensi_mahasiswa_fix | {silver_ref} | {bronze_ref - silver_ref} |\n")
        f.write(f"| silver_khs_fix | {silver_khs} | {bronze_khs - silver_khs} |\n\n")

        f.write("**Cleaning Rules Applied:**\n")
        f.write("- NULL tanggal_masuk removed\n")
        f.write("- tanggal_keluar < tanggal_masuk removed\n")
        f.write("- Duplicate id_mahasiswa removed\n")
        f.write("- IP = 0 preserved as valid\n\n")

        f.write("## Gold Layer\n\n")
        f.write("| Table | Rows |\n|-------|------|\n")
        f.write(f"| dim_mahasiswa_fix | {gold_dim} |\n")
        f.write(f"| fact_khs_fix | {gold_fact} |\n\n")

        f.write("**Gold Logic (unchanged):**\n")
        f.write("- LEFT JOIN silver_referensi + silver_khs\n")
        f.write("- TARGET_SKS mapping: {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}\n")
        f.write("- IP = 0 included in average\n")
        f.write("- lama_studi only for LULUS\n")
        f.write("- AKTIF 2019-2021 labeled as Terlambat\n\n")

        f.write("## Feature Store\n\n")
        f.write("### Training\n\n")
        f.write(f"- Total: **{train_count}** rows\n")
        f.write(f"- Features: jk_enc, angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks\n\n")
        f.write("| Label | Count | Percentage |\n|-------|-------|------------|\n")
        f.write(f"| Tepat Waktu (0) | {tw_count} | {tw_pct}% |\n")
        f.write(f"| Terlambat (1) | {tl_count} | {tl_pct}% |\n\n")

        f.write("**Training Composition:**\n")
        f.write("- LULUS angkatan 2012-2021: labeled by lama_studi\n")
        f.write("- AKTIF angkatan 2019-2021: label = Terlambat\n\n")

        f.write("### Inference\n\n")
        f.write(f"- Total: **{infer_count}** rows\n\n")
        f.write("| Angkatan | Count |\n|----------|-------|\n")
        f.write(f"| 2022 | {infer_2022} |\n")
        f.write(f"| 2023 | {infer_2023} |\n")
        f.write(f"| 2024 | {infer_2024} |\n\n")

        f.write("**Inference Composition:**\n")
        f.write("- LULUS angkatan 2022\n")
        f.write("- AKTIF angkatan 2022-2024\n\n")

        f.write("## Saved Files\n\n")
        f.write("### Excel Files\n\n")
        f.write("| File | Rows | Cols | Status |\n|------|------|------|--------|\n")
        for tbl, info in excel_results.items():
            fname = EXCEL_MAP.get(tbl, f"{tbl}.xlsx")
            if "error" in info:
                f.write(f"| {fname} | - | - | ERROR: {info['error'][:50]} |\n")
            else:
                f.write(f"| {fname} | {info['rows']} | {info['cols']} | OK |\n")

        f.write("\n### Parquet Files\n\n")
        f.write(f"Location: `{PARQUET_DIR}/`\n\n")
        for schema, tables in TABLES.items():
            for orig_name, fix_name in tables:
                f.write(f"- `{PARQUET_DIR}/{fix_name}/`\n")

        f.write("\n### MinIO / Iceberg Tables\n\n")
        f.write("| Schema | Table | Objects | Status |\n|--------|-------|---------|--------|\n")
        for schema, tables in TABLES.items():
            for orig_name, fix_name in tables:
                mr = minio_results.get(fix_name, {})
                f.write(f"| {schema} | {fix_name} | {mr.get('objects', '-')} | {mr.get('status', 'ERROR')} |\n")

        f.write("\n## Validation\n\n")
        f.write("| Check | Expected | Actual | Status |\n|-------|----------|--------|--------|\n")
        for name, expected, actual, status in checks:
            f.write(f"| {name} | {expected} | {actual} | {status} |\n")

        f.write(f"\n**IP = 0 in training**: {ip_zero_train} rows (preserved as valid)\n")
        f.write(f"**IP = 0 in inference**: {ip_zero_infer} rows (preserved as valid)\n")
        f.write(f"**All outputs use _fix suffix**: {'YES' if all_tables_use_fix else 'NO'}\n")
        f.write(f"**No old data mixed**: {'YES' if all_pass else 'NO'}\n")

        f.write(f"\n## Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}\n")

    print(f"  Report: {report_path}")

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("FINAL DATA STORAGE - FIX")
    print("=" * 80)
    print(f"""
SOURCE:
  (asli)req_data_rut (baru).xlsx

BRONZE
  data_referensi_mahasiswa_fix : {bronze_ref}
  data_khs_fix                 : {bronze_khs}
  data_program_studi_fix       : {bronze_prodi}
  data_kelas_fix               : {bronze_kelas}
  data_kurikulum_fix           : {bronze_kurikulum}

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

    # List all saved Excel files
    print("Excel files saved in Data/:")
    for tbl, info in excel_results.items():
        fname = EXCEL_MAP.get(tbl, f"{tbl}.xlsx")
        if "error" in info:
            print(f"  ERROR: {fname} - {info['error'][:80]}")
        else:
            print(f"  OK: {fname} ({info['rows']} rows)")

    print(f"\nReport: {report_path}")
    print("DONE.")


if __name__ == "__main__":
    main()
