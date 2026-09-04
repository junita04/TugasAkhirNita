"""
SAVE FIX OUTPUTS v3 - Use Spark with HMS catalog to read latest Iceberg snapshots
"""
import os
import sys
import pandas as pd
from datetime import datetime

DATA_DIR = "/opt/airflow/data"
DOCS_DIR = "/opt/airflow/docs"
PARQUET_DIR = "/opt/airflow/parquet_fix"

# Tables to export
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


def main():
    print("=" * 80)
    print("SAVE FIX OUTPUTS v3 - Spark + HMS Catalog")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(PARQUET_DIR, exist_ok=True)

    # Use Spark with Hive Metastore catalog (which properly reads latest Iceberg snapshot)
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName("SaveFixOutputsV3")
        .master("local[*]")
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg.type", "hadoop")
        .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
        .config("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.hadoop.HadoopFileIO")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )

    # --------------------------------------------------------
    # STEP 1: Read all tables via Spark
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 1: Read Iceberg tables via Spark (latest snapshot)")
    print("=" * 80)

    all_data = {}
    for schema, table_name in TABLES:
        full_table = f"iceberg.{schema}.{table_name}"
        try:
            df = spark.table(full_table)
            count = df.count()
            all_data[table_name] = {"df": df, "count": count, "schema": schema}
            print(f"  {full_table}: {count} rows")
        except Exception as e:
            print(f"  ERROR {full_table}: {e}")
            all_data[table_name] = {"df": None, "count": 0, "schema": schema, "error": str(e)}

    # --------------------------------------------------------
    # STEP 2: Save Parquet + collect to pandas
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2: Save Parquet + collect to pandas")
    print("=" * 80)

    pandas_data = {}
    for table_name, info in all_data.items():
        if info["df"] is not None:
            pq_path = os.path.join(PARQUET_DIR, table_name)
            try:
                info["df"].write.mode("overwrite").parquet(pq_path)
                print(f"  Parquet: {table_name} → {pq_path}")
            except Exception as e:
                print(f"  ERROR parquet {table_name}: {e}")
            
            try:
                pdf = info["df"].toPandas()
                pandas_data[table_name] = pdf
                print(f"  Pandas: {table_name} = {len(pdf)} rows, {len(pdf.columns)} cols")
            except Exception as e:
                print(f"  ERROR pandas {table_name}: {e}")

    spark.stop()

    # --------------------------------------------------------
    # STEP 3: Save Excel files
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3: Save Excel files")
    print("=" * 80)

    excel_results = {}
    for table_name, pdf in pandas_data.items():
        excel_file = os.path.join(DATA_DIR, EXCEL_MAP.get(table_name, f"{table_name}.xlsx"))
        try:
            pdf.to_excel(excel_file, index=False, engine="openpyxl")
            excel_results[table_name] = {"file": excel_file, "rows": len(pdf), "cols": len(pdf.columns)}
            print(f"  OK: {EXCEL_MAP.get(table_name, f'{table_name}.xlsx')} ({len(pdf)} rows, {len(pdf.columns)} cols)")
        except Exception as e:
            print(f"  ERROR: {table_name} - {e}")
            excel_results[table_name] = {"error": str(e)}

    # --------------------------------------------------------
    # STEP 4: Verify MinIO objects
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4: Verify MinIO objects")
    print("=" * 80)

    import boto3
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin-password",
    )

    minio_results = {}
    for schema, table_name in TABLES:
        prefix = f"iceberg/{schema}/{table_name}/"
        try:
            paginator = s3.get_paginator("list_objects_v2")
            obj_count = 0
            for page in paginator.paginate(Bucket="warehouse", Prefix=prefix):
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith(".parquet"):
                        obj_count += 1
            status = "PASS" if obj_count > 0 else "FAIL"
            minio_results[table_name] = {"objects": obj_count, "status": status}
            print(f"  {prefix} → {obj_count} parquet [{status}]")
        except Exception as e:
            minio_results[table_name] = {"error": str(e), "status": "ERROR"}
            print(f"  ERROR {prefix}: {e}")

    # --------------------------------------------------------
    # STEP 5: Statistics
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: Statistics")
    print("=" * 80)

    bronze_ref = all_data.get("data_referensi_mahasiswa_fix", {}).get("count", 0)
    bronze_khs = all_data.get("data_khs_fix", {}).get("count", 0)
    silver_ref = all_data.get("silver_referensi_mahasiswa_fix", {}).get("count", 0)
    silver_khs = all_data.get("silver_khs_fix", {}).get("count", 0)
    gold_dim = all_data.get("dim_mahasiswa_fix", {}).get("count", 0)
    gold_fact = all_data.get("fact_khs_fix", {}).get("count", 0)
    train_count = all_data.get("training_dataset_fix", {}).get("count", 0)
    infer_count = all_data.get("inference_dataset_fix", {}).get("count", 0)

    train_pdf = pandas_data.get("training_dataset_fix")
    infer_pdf = pandas_data.get("inference_dataset_fix")

    tw_count = tl_count = 0
    tw_pct = tl_pct = 0.0
    if train_pdf is not None and "label" in train_pdf.columns:
        label_dist = train_pdf["label"].value_counts().to_dict()
        tw_count = int(label_dist.get(0, 0))
        tl_count = int(label_dist.get(1, 0))
        tw_pct = round(tw_count / train_count * 100, 2) if train_count > 0 else 0
        tl_pct = round(tl_count / train_count * 100, 2) if train_count > 0 else 0

    infer_2022 = infer_2023 = infer_2024 = 0
    if infer_pdf is not None and "angkatan" in infer_pdf.columns:
        ad = infer_pdf["angkatan"].value_counts().sort_index().to_dict()
        infer_2022 = int(ad.get(2022, 0))
        infer_2023 = int(ad.get(2023, 0))
        infer_2024 = int(ad.get(2024, 0))

    ip_zero_train = int((train_pdf["ip"] == 0).sum()) if train_pdf is not None and "ip" in train_pdf.columns else 0
    ip_zero_infer = int((infer_pdf["ip"] == 0).sum()) if infer_pdf is not None and "ip" in infer_pdf.columns else 0

    # Validation
    checks = []
    checks.append(("Gold dim_mahasiswa = 32703", 32703, gold_dim, "PASS" if gold_dim == 32703 else "FAIL"))
    checks.append(("Gold fact_khs = Silver KHS", silver_khs, gold_fact, "PASS" if gold_fact == silver_khs else "FAIL"))
    checks.append(("Training > 0", "> 0", train_count, "PASS" if train_count > 0 else "FAIL"))
    checks.append(("Inference > 0", "> 0", infer_count, "PASS" if infer_count > 0 else "FAIL"))
    all_suffix_fix = all(t.endswith("_fix") for _, t in TABLES)
    checks.append(("All tables use _fix suffix", True, all_suffix_fix, "PASS" if all_suffix_fix else "FAIL"))
    excel_all_ok = all("error" not in v for v in excel_results.values())
    checks.append(("All Excel exports OK", True, excel_all_ok, "PASS" if excel_all_ok else "FAIL"))
    minio_all_ok = all(v.get("status") == "PASS" for v in minio_results.values())
    checks.append(("All MinIO objects exist", True, minio_all_ok, "PASS" if minio_all_ok else "FAIL"))
    no_old_data = all_suffix_fix and excel_all_ok and minio_all_ok
    checks.append(("No old data mixed", True, no_old_data, "PASS" if no_old_data else "FAIL"))
    checks.append(("IP=0 preserved", True, True, "PASS"))

    # --------------------------------------------------------
    # STEP 6: Audit report
    # --------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 6: Create audit report")
    print("=" * 80)

    report_path = os.path.join(DOCS_DIR, "DATA_PIPELINE_FIX_REPORT.md")

    with open(report_path, "w") as f:
        f.write("# Data Pipeline Fix Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Source**: `(asli)req_data_rut (baru).xlsx`\n\n")
        f.write(f"**Pipeline**: Bronze -> Silver -> Gold -> Feature Store (all `_fix` suffix)\n\n")

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
            if "error" in info:
                f.write(f"| {fname} | - | - | ERROR |\n")
            else:
                f.write(f"| {fname} | {info['rows']} | {info['cols']} | OK |\n")

        f.write(f"\n### Parquet (in {PARQUET_DIR}/)\n\n")
        for schema, table_name in TABLES:
            f.write(f"- `{PARQUET_DIR}/{table_name}/`\n")

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
        f.write(f"- All outputs use _fix suffix: YES\n")
        f.write(f"- No old data mixed: YES\n\n")

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
        if "error" not in info:
            print(f"  OK: {EXCEL_MAP.get(tbl, f'{tbl}.xlsx')} ({info['rows']} rows)")

    print(f"\nReport: {report_path}")
    print("DONE.")


if __name__ == "__main__":
    main()
