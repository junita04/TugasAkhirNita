"""
Full Pipeline Fix - Bronze → Silver → Gold → Feature Store
==========================================================
Source: (asli)req_data_rut (baru).xlsx
All tables use _fix suffix.
NO ML training, NO inference, NO model changes.
"""
import sys, gc, time, json
sys.path.insert(0, '/opt/airflow')

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
EXCEL = Path('/opt/airflow/data/(asli)req_data_rut (baru).xlsx')
REPORT_DIR = Path('/opt/airflow/docs')
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SUFFIX = "_fix"
NS = "iceberg"

# TARGET_SKS from existing system
TARGET_SKS = {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}

# Snapshot semester (Januari 2026)
SNAPSHOT_SEMESTER = {2022:7, 2023:5, 2024:3}

# 8 Features
FEATURE_X = ["jk_enc","angkatan","ip","ipk","total_sks","jumlah_mk","sks_seharusnya","selisih_sks"]

# Sheet mapping
SHEET_MAP = {
    "Referensi Data Mahasiswa": "data_referensi_mahasiswa",
    "Data KHS": "data_khs",
    "Data Program Studi": "data_program_studi",
    "Data Kelas": "data_kelas",
    "Data Kurikulum": "data_kurikulum",
}

# Silver column mapping
SILVER_COL_MAP = {
    "data_referensi_mahasiswa": {
        "ID_MHS": "id_mahasiswa", "Jenis Kelamin": "jenis_kelamin",
        "Tanggal Masuk": "tanggal_masuk", "Tanggal Keluar": "tanggal_keluar",
        "IPK": "ipk", "Total SKS": "total_sks", "Jumlah MK": "jumlah_mk",
        "Status Mahasiswa": "status_mahasiswa",
    },
    "data_khs": {
        "ID_MHS": "id_mahasiswa", "IP": "ip", "SKS": "sks",
    },
}

from backend.spark.session import get_spark

def get_spark_session(name):
    return get_spark(name)

# ============================================================
# STEP 1: BRONZE
# ============================================================
def run_bronze():
    print("=" * 80)
    print("STEP 1: BRONZE LAYER")
    print("=" * 80)

    xl = pd.ExcelFile(EXCEL)
    report = {"tables": {}}

    # Read all sheets with pandas → parquet
    temp_dir = Path('/opt/airflow/data/temp_bronze_fix')
    temp_dir.mkdir(parents=True, exist_ok=True)

    for sheet in xl.sheet_names:
        if sheet not in SHEET_MAP:
            continue
        tname = SHEET_MAP[sheet]
        df = pd.read_excel(EXCEL, sheet_name=sheet)
        if df.empty or len(df.columns) == 0:
            print(f"  SKIP: {sheet} (empty)")
            continue
        p = temp_dir / f"{tname}.parquet"
        df.to_parquet(p, index=False)
        report["tables"][tname] = {"rows": len(df), "cols": len(df.columns)}
        print(f"  {sheet} → {tname}: {len(df)} rows, {len(df.columns)} cols")

    # Load parquet → Iceberg Bronze with _fix suffix
    spark = get_spark_session("Bronze Fix")
    for tname, info in report["tables"].items():
        p = temp_dir / f"{tname}.parquet"
        df_spark = spark.read.parquet(str(p)).coalesce(1)
        full = f"{NS}.bronze.{tname}{SUFFIX}"
        spark.sql(f"DROP TABLE IF EXISTS {full}")
        df_spark.write.format("iceberg").mode("overwrite").saveAsTable(full)
        actual = spark.table(full).count()
        info["iceberg_count"] = actual
        print(f"  Iceberg: {full} = {actual} rows")
    spark.stop()

    # Write report
    with open(REPORT_DIR / "01_bronze_report_fix.md", "w") as f:
        f.write("# Bronze Layer Report (fix)\n\n")
        f.write(f"**Source**: `(asli)req_data_rut (baru).xlsx`\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Tables\n\n")
        f.write("| Table | Rows | Cols | Iceberg |\n|-------|------|------|----------|\n")
        for tname, info in report["tables"].items():
            f.write(f"| {tname} | {info['rows']} | {info['cols']} | {info.get('iceberg_count', 'N/A')} |\n")
        f.write("\n## Notes\n\n")
        f.write("- IP = 0 is preserved as valid data\n")
        f.write("- No data transformation applied\n")
        f.write("- Raw data from Excel loaded directly\n")
    print(f"  Report: 01_bronze_report_fix.md")
    return report

# ============================================================
# STEP 2: SILVER
# ============================================================
def run_silver(bronze_report):
    print("\n" + "=" * 80)
    print("STEP 2: SILVER LAYER")
    print("=" * 80)

    spark = get_spark_session("Silver Fix")
    report = {"tables": {}}

    # Process each bronze table
    for bronze_tname, col_map in SILVER_COL_MAP.items():
        silver_tname = f"silver_{bronze_tname.replace('data_', '')}{SUFFIX}"
        full_bronze = f"{NS}.bronze.{bronze_tname}{SUFFIX}"
        full_silver = f"{NS}.silver.{silver_tname}"

        print(f"\n  Processing: {bronze_tname} → {silver_tname}")
        df = spark.table(full_bronze)
        initial_count = df.count()

        # Apply column mapping
        for old_name, new_name in col_map.items():
            if old_name in [c for c in df.columns]:
                df = df.withColumnRenamed(old_name, new_name)

        # Trim string columns
        from pyspark.sql import functions as F
        for field in df.schema.fields:
            if field.dataType.simpleString() == "string":
                df = df.withColumn(field.name, F.trim(F.col(field.name)))

        # Drop all-null rows
        df = df.na.drop(how="all")

        # Type casting
        if "tanggal_masuk" in [c for c in df.columns]:
            df = df.withColumn("tanggal_masuk", F.col("tanggal_masuk").cast("date"))
        if "tanggal_keluar" in [c for c in df.columns]:
            df = df.withColumn("tanggal_keluar", F.col("tanggal_keluar").cast("date"))
        if "ipk" in [c for c in df.columns]:
            df = df.withColumn("ipk", F.col("ipk").cast("double"))
        if "total_sks" in [c for c in df.columns]:
            df = df.withColumn("total_sks", F.col("total_sks").cast("int"))
        if "jumlah_mk" in [c for c in df.columns]:
            df = df.withColumn("jumlah_mk", F.col("jumlah_mk").cast("int"))
        if "ip" in [c for c in df.columns]:
            df = df.withColumn("ip", F.col("ip").cast("double"))
        if "sks" in [c for c in df.columns]:
            df = df.withColumn("sks", F.col("sks").cast("int"))

        # Special processing for mahasiswa
        if bronze_tname == "data_referensi_mahasiswa":
            # Remove rows where tanggal_masuk is NULL
            before = df.count()
            df = df.filter(F.col("tanggal_masuk").isNotNull())
            after = df.count()
            removed = before - after
            print(f"    Removed NULL tanggal_masuk: {removed} rows")

            # Remove rows where tanggal_keluar < tanggal_masuk
            before2 = df.count()
            df = df.filter(
                F.col("tanggal_keluar").isNull() |
                (F.col("tanggal_keluar") >= F.col("tanggal_masuk"))
            )
            after2 = df.count()
            removed2 = before2 - after2
            print(f"    Removed keluar < masuk: {removed2} rows")

            # Remove duplicates by id_mahasiswa
            before3 = df.count()
            df = df.dropDuplicates(["id_mahasiswa"])
            after3 = df.count()
            removed3 = before3 - after3
            print(f"    Removed duplicates: {removed3} rows")

            # IP=0: keep as valid (do NOT filter)
            ip_zero = df.filter(F.col("ipk") == 0).count() if "ipk" in [c for c in df.columns] else 0
            print(f"    IPK = 0 preserved: {ip_zero} rows")

        # Special processing for KHS
        if bronze_tname == "data_khs":
            # Keep IP=0 as valid
            ip_zero_khs = df.filter(F.col("ip") == 0).count() if "ip" in [c for c in df.columns] else 0
            print(f"    IP = 0 preserved in KHS: {ip_zero_khs} rows")

            # Remove null id_mahasiswa, ip, sks
            before = df.count()
            df = df.filter(
                F.col("id_mahasiswa").isNotNull() &
                F.col("ip").isNotNull() &
                F.col("sks").isNotNull()
            )
            after = df.count()
            print(f"    Removed null id/ip/sks: {before - after} rows")

        final_count = df.count()
        report["tables"][silver_tname] = {
            "bronze_count": initial_count,
            "silver_count": final_count,
            "removed": initial_count - final_count,
        }

        # Write to Iceberg
        df.writeTo(full_silver).using("iceberg").createOrReplace()
        print(f"    Written: {full_silver} = {final_count} rows")

    spark.stop()

    # Write report
    with open(REPORT_DIR / "02_silver_report_fix.md", "w") as f:
        f.write("# Silver Layer Report (fix)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Processing\n\n")
        f.write("- Column names standardized (lowercase, underscore)\n")
        f.write("- Type casting applied\n")
        f.write("- NULL tanggal_masuk removed\n")
        f.write("- tanggal_keluar < tanggal_masuk removed\n")
        f.write("- Duplicate id_mahasiswa removed\n")
        f.write("- IP = 0 preserved as valid\n\n")
        f.write("## Tables\n\n")
        f.write("| Silver Table | Bronze Count | Silver Count | Removed |\n|-------------|-------------|-------------|----------|\n")
        for tname, info in report["tables"].items():
            f.write(f"| {tname} | {info['bronze_count']} | {info['silver_count']} | {info['removed']} |\n")
    print(f"  Report: 02_silver_report_fix.md")
    return report

# ============================================================
# STEP 3: GOLD
# ============================================================
def run_gold(silver_report):
    print("\n" + "=" * 80)
    print("STEP 3: GOLD LAYER")
    print("=" * 80)

    spark = get_spark_session("Gold Fix")
    from pyspark.sql import functions as F
    from pyspark.sql.types import IntegerType

    report = {}

    # ---- Gold Fact KHS (agregasi per mahasiswa) ----
    print("\n  Building gold.fact_khs_fix...")
    khs = spark.table(f"{NS}.silver.silver_khs{SUFFIX}")
    khs_count = khs.count()
    print(f"    Silver KHS: {khs_count} rows")

    # Agregasi: avg(ip), sum(sks), count(*)
    # IP=0 is included in average
    fact = khs.groupBy("id_mahasiswa").agg(
        F.round(F.avg("ip"), 4).alias("ip"),
        F.sum("sks").alias("sks_khs"),
        F.count("*").alias("jumlah_data_khs"),
    )
    fact_count = fact.count()
    print(f"    Unique mahasiswa with KHS: {fact_count}")

    full_fact = f"{NS}.gold.fact_khs{SUFFIX}"
    fact.writeTo(full_fact).using("iceberg").createOrReplace()
    print(f"    Written: {full_fact} = {fact_count} rows")

    # ---- Gold Dim Mahasiswa (star schema) ----
    print("\n  Building gold.dim_mahasiswa_fix...")
    mhs = spark.table(f"{NS}.silver.silver_referensi_mahasiswa{SUFFIX}")
    mhs_count = mhs.count()
    print(f"    Silver mahasiswa: {mhs_count}")

    # LEFT JOIN: all mahasiswa + KHS aggregation
    dim = mhs.join(fact, on="id_mahasiswa", how="left")
    dim = dim.dropDuplicates(["id_mahasiswa"])
    dim_count = dim.count()
    print(f"    After LEFT JOIN + dedup: {dim_count}")

    # Derive: angkatan from tahun tanggal_masuk
    dim = dim.withColumn("angkatan", F.year(F.col("tanggal_masuk")))

    # Derive: semester based on months elapsed from tanggal_masuk
    months_elapsed = F.months_between(F.current_date(), F.col("tanggal_masuk"))
    dim = dim.withColumn("semester_raw", F.floor(months_elapsed / F.lit(6)) + F.lit(1))
    dim = dim.withColumn("semester",
        F.when(F.col("semester_raw") < 1, F.lit(1))
         .when(F.col("semester_raw") > 8, F.lit(8))
         .otherwise(F.col("semester_raw"))
         .cast(IntegerType())
    )
    dim = dim.drop("semester_raw")

    # Derive: sks_seharusnya from TARGET_SKS mapping
    when_expr = F.lit(None).cast(IntegerType())
    for sem, sks in sorted(TARGET_SKS.items()):
        when_expr = F.when(F.col("semester") == sem, sks).otherwise(when_expr)
    dim = dim.withColumn("sks_seharusnya", when_expr)

    # Derive: selisih_sks
    dim = dim.withColumn("selisih_sks", F.col("total_sks") - F.col("sks_seharusnya"))

    # Derive: lama_studi (only for LULUS)
    dim = dim.withColumn("lama_studi",
        F.when(
            F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS",
            F.round(F.datediff(F.col("tanggal_keluar"), F.col("tanggal_masuk")) / F.lit(365), 2)
        )
    )

    # Derive: status_kelulusan + label
    dim = dim.withColumn("status_kelulusan",
        F.when(
            F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS",
            F.when(F.col("lama_studi") <= 4, F.lit("Tepat Waktu"))
             .otherwise(F.lit("Terlambat"))
        ).when(
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF") &
            (F.col("angkatan").isin(2019, 2020, 2021)),
            F.lit("Terlambat")
        )
    )

    dim = dim.withColumn("label",
        F.when(F.col("status_kelulusan") == "Tepat Waktu", F.lit(0))
         .when(F.col("status_kelulusan") == "Terlambat", F.lit(1))
         .cast(IntegerType())
    )

    # Validation
    final_count = dim.count()
    unique_count = dim.select("id_mahasiswa").distinct().count()

    # KHS coverage
    khs_in_dim = dim.filter(F.col("ip").isNotNull()).count()

    print(f"\n    VALIDATION:")
    print(f"    Total Gold: {final_count}")
    print(f"    Unique ID: {unique_count}")
    print(f"    Mahasiswa with KHS: {khs_in_dim}")

    # Status distribution
    status_dist = dim.groupBy("status_mahasiswa").count().collect()
    print(f"    Status distribution:")
    for row in status_dist:
        print(f"      {row['status_mahasiswa']}: {row['count']}")

    # Label distribution
    label_dist = dim.filter(F.col("label").isNotNull()).groupBy("label").count().collect()
    print(f"    Label distribution:")
    for row in label_dist:
        label_name = "TW" if row['label'] == 0 else "TL"
        print(f"      {label_name}: {row['count']}")

    report = {
        "silver_mahasiswa": mhs_count,
        "silver_khs": khs_count,
        "gold_count": final_count,
        "unique_count": unique_count,
        "khs_coverage": khs_in_dim,
        "status_dist": {row['status_mahasiswa']: row['count'] for row in status_dist},
        "label_dist": {row['label']: row['count'] for row in label_dist},
    }

    # Write to Iceberg
    full_dim = f"{NS}.gold.dim_mahasiswa{SUFFIX}"
    dim.writeTo(full_dim).using("iceberg").createOrReplace()
    print(f"\n    Written: {full_dim} = {final_count} rows")

    spark.stop()

    # Write report
    with open(REPORT_DIR / "03_gold_report_fix.md", "w") as f:
        f.write("# Gold Layer Report (fix)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## JOIN Validation\n\n")
        f.write(f"- Silver mahasiswa: {mhs_count}\n")
        f.write(f"- Silver KHS: {khs_count}\n")
        f.write(f"- Unique KHS mahasiswa: {fact_count}\n")
        f.write(f"- Gold (after LEFT JOIN): {final_count}\n")
        f.write(f"- Unique ID Gold: {unique_count}\n")
        f.write(f"- Mahasiswa with KHS: {khs_in_dim}\n\n")
        f.write("## Status Distribution\n\n")
        f.write("| Status | Count |\n|--------|-------|\n")
        for k, v in report["status_dist"].items():
            f.write(f"| {k} | {v} |\n")
        f.write("\n## Label Distribution (Training)\n\n")
        f.write("| Label | Count |\n|-------|-------|\n")
        for k, v in report["label_dist"].items():
            label_name = "Tepat Waktu" if k == 0 else "Terlambat"
            f.write(f"| {label_name} | {v} |\n")
        f.write(f"\n## TARGET_SKS Mapping\n\n")
        f.write("| Semester | Target SKS |\n|----------|------------|\n")
        for sem, sks in sorted(TARGET_SKS.items()):
            f.write(f"| {sem} | {sks} |\n")
        f.write("\n## Notes\n\n")
        f.write("- IP = 0 included in average calculation\n")
        f.write("- LEFT JOIN preserves all mahasiswa\n")
        f.write("- lama_studi only for LULUS\n")
        f.write("- AKTIF 2019-2021 labeled as Terlambat\n")
    print(f"  Report: 03_gold_report_fix.md")
    return report

# ============================================================
# STEP 4: FEATURE STORE
# ============================================================
def run_feature_store(gold_report):
    print("\n" + "=" * 80)
    print("STEP 4: FEATURE STORE")
    print("=" * 80)

    spark = get_spark_session("Feature Store Fix")
    from pyspark.sql import functions as F

    dim = spark.table(f"{NS}.gold.dim_mahasiswa{SUFFIX}")
    total = dim.count()
    print(f"  Gold dim_mahasiswa: {total}")

    # Derive jk_enc
    dim = dim.withColumn("jk_enc",
        F.when(F.upper(F.trim(F.col("jenis_kelamin"))).isin("P", "PEREMPUAN"), F.lit(0))
         .when(F.upper(F.trim(F.col("jenis_kelamin"))).isin("L", "LAKI-LAKI", "LAKI LAKI", "LAKI"), F.lit(1))
    )

    # ---- TRAINING ----
    print("\n  --- TRAINING ---")
    # Training = LULUS (all years) + AKTIF 2019-2021
    training = dim.filter(
        (F.col("label").isNotNull()) &
        (
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS") |
            (
                (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF") &
                (F.col("angkatan").isin(2019, 2020, 2021))
            )
        )
    )

    # Drop rows where any of the 8 features is NULL
    training_before = training.count()
    training = training.dropna(subset=FEATURE_X)
    training_after = training.count()
    print(f"    Before dropna: {training_before}")
    print(f"    After dropna: {training_after}")
    print(f"    Removed by dropna: {training_before - training_after}")

    # Deduplicate
    training = training.dropDuplicates(["id_mahasiswa"])
    training_final = training.select("id_mahasiswa", *FEATURE_X, "label")
    train_count = training_final.count()

    # Distribution
    train_dist = training_final.groupBy("label").count().collect()
    train_angkatan = training_final.groupBy("angkatan").count().orderBy("angkatan").collect()
    train_status = training.groupBy("status_mahasiswa").count().collect()

    print(f"    Training count: {train_count}")
    print(f"    Label distribution:")
    for row in train_dist:
        label_name = "TW" if row['label'] == 0 else "TL"
        print(f"      {label_name}: {row['count']}")
    print(f"    Angkatan distribution:")
    for row in train_angkatan:
        print(f"      {row['angkatan']}: {row['count']}")
    print(f"    Status distribution:")
    for row in train_status:
        print(f"      {row['status_mahasiswa']}: {row['count']}")

    # Check for forbidden data
    aktif_2022_2024_in_train = training_final.filter(
        (F.col("angkatan").isin(2022, 2023, 2024)) &
        (training_final["jk_enc"].isNotNull())  # just to keep filter syntax
    ).count()
    # Simpler check
    aktif_recent = training.join(
        dim.filter(
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF") &
            (F.col("angkatan").isin(2022, 2023, 2024))
        ), on="id_mahasiswa", how="inner"
    ).count()
    print(f"    AKTIF 2022-2024 in training: {aktif_recent} (should be 0)")

    # Write training
    full_train = f"{NS}.feature_store.training_dataset{SUFFIX}"
    training_final.writeTo(full_train).using("iceberg").createOrReplace()
    print(f"    Written: {full_train} = {train_count} rows")

    # ---- INFERENCE ----
    print("\n  --- INFERENCE ---")
    # Inference = LULUS 2022 + AKTIF 2022-2024
    inference = dim.filter(
        (
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS") &
            (F.col("angkatan") == 2022)
        ) |
        (
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF") &
            (F.col("angkatan").isin(2022, 2023, 2024))
        )
    )

    # Apply snapshot semester for inference
    semester_when = F.lit(None).cast("int")
    for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
        semester_when = F.when(F.col("angkatan") == angkatan, sem).otherwise(semester_when)
    inference = inference.withColumn("semester", semester_when)

    # Apply snapshot sks_seharusnya
    sks_when = F.lit(None).cast("int")
    for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
        sks = TARGET_SKS[sem]
        sks_when = F.when(F.col("angkatan") == angkatan, sks).otherwise(sks_when)
    inference = inference.withColumn("sks_seharusnya", sks_when)

    # Recalculate selisih_sks for inference
    inference = inference.withColumn("selisih_sks", F.col("total_sks") - F.col("sks_seharusnya"))

    # Drop NULL features
    inf_before = inference.count()
    inference = inference.dropna(subset=FEATURE_X)
    inf_after = inference.count()
    print(f"    Before dropna: {inf_before}")
    print(f"    After dropna: {inf_after}")

    # Deduplicate
    inference = inference.dropDuplicates(["id_mahasiswa"])
    inf_final = inference.select("id_mahasiswa", *FEATURE_X)
    inf_count = inf_final.count()

    # Distribution
    inf_angkatan = inf_final.groupBy("angkatan").count().orderBy("angkatan").collect()
    inf_status = inference.groupBy("status_mahasiswa").count().collect()

    print(f"    Inference count: {inf_count}")
    print(f"    Angkatan distribution:")
    for row in inf_angkatan:
        print(f"      {row['angkatan']}: {row['count']}")
    print(f"    Status distribution:")
    for row in inf_status:
        print(f"      {row['status_mahasiswa']}: {row['count']}")

    # Check for training data in inference
    training_in_inf = inference.join(
        training_final.select("id_mahasiswa"), on="id_mahasiswa", how="inner"
    ).count()
    print(f"    Training data in inference: {training_in_inf} (should be 0)")

    # Write inference
    full_inf = f"{NS}.feature_store.inference_dataset{SUFFIX}"
    inf_final.writeTo(full_inf).using("iceberg").createOrReplace()
    print(f"    Written: {full_inf} = {inf_count} rows")

    spark.stop()

    # Write reports
    # Training report
    with open(REPORT_DIR / "04_feature_store_training_report_fix.md", "w") as f:
        f.write("# Feature Store Training Report (fix)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total training: {train_count}\n")
        f.write(f"- Features: {FEATURE_X}\n\n")
        f.write("## Label Distribution\n\n")
        f.write("| Label | Count |\n|-------|-------|\n")
        for row in train_dist:
            label_name = "Tepat Waktu (0)" if row['label'] == 0 else "Terlambat (1)"
            f.write(f"| {label_name} | {row['count']} |\n")
        f.write("\n## Angkatan Distribution\n\n")
        f.write("| Angkatan | Count |\n|----------|-------|\n")
        for row in train_angkatan:
            f.write(f"| {row['angkatan']} | {row['count']} |\n")
        f.write("\n## Status Distribution\n\n")
        f.write("| Status | Count |\n|--------|-------|\n")
        for row in train_status:
            f.write(f"| {row['status_mahasiswa']} | {row['count']} |\n")
        f.write("\n## Validation\n\n")
        f.write(f"- AKTIF 2022-2024 in training: {aktif_recent} (must be 0)\n")
        f.write(f"- NULL features after dropna: 0\n")
        f.write(f"- Duplicate IDs: 0\n")
        f.write("\n## Composition\n\n")
        f.write("- LULUS angkatan 2012-2021: labeled by lama_studi\n")
        f.write("- AKTIF angkatan 2019-2021: label = Terlambat\n")

    # Inference report
    with open(REPORT_DIR / "05_feature_store_inference_report_fix.md", "w") as f:
        f.write("# Feature Store Inference Report (fix)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total inference: {inf_count}\n")
        f.write(f"- Features: {FEATURE_X}\n\n")
        f.write("## Angkatan Distribution\n\n")
        f.write("| Angkatan | Count |\n|----------|-------|\n")
        for row in inf_angkatan:
            f.write(f"| {row['angkatan']} | {row['count']} |\n")
        f.write("\n## Status Distribution\n\n")
        f.write("| Status | Count |\n|--------|-------|\n")
        for row in inf_status:
            f.write(f"| {row['status_mahasiswa']} | {row['count']} |\n")
        f.write("\n## Validation\n\n")
        f.write(f"- Training data in inference: {training_in_inf} (must be 0)\n")
        f.write(f"- NULL features after dropna: 0\n")
        f.write(f"- Duplicate IDs: 0\n")
        f.write("\n## Snapshot (Januari 2026)\n\n")
        f.write("| Angkatan | Semester | Target SKS |\n|----------|----------|------------|\n")
        for a, s in sorted(SNAPSHOT_SEMESTER.items()):
            f.write(f"| {a} | {s} | {TARGET_SKS[s]} |\n")

    print(f"  Reports: 04_feature_store_training_report_fix.md, 05_feature_store_inference_report_fix.md")
    return {"training": train_count, "inference": inf_count}

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 80)
    print("FULL PIPELINE FIX - Bronze → Silver → Gold → Feature Store")
    print("=" * 80)
    print(f"Source: {EXCEL}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    bronze_report = run_bronze()
    silver_report = run_silver(bronze_report)
    gold_report = run_gold(silver_report)
    fs_report = run_feature_store(gold_report)

    # Final validation
    print("\n" + "=" * 80)
    print("FINAL VALIDATION")
    print("=" * 80)

    print(f"""
LAYER                     DATA
--------------------------------------------------
Bronze (referensi)        {bronze_report['tables'].get('data_referensi_mahasiswa', {}).get('iceberg_count', 'N/A')}
Bronze (KHS)              {bronze_report['tables'].get('data_khs', {}).get('iceberg_count', 'N/A')}
Silver (mahasiswa)        {silver_report['tables'].get(f'silver_mahasiswa{SUFFIX}', {}).get('silver_count', 'N/A')}
Silver (KHS)              {silver_report['tables'].get(f'silver_khs{SUFFIX}', {}).get('silver_count', 'N/A')}
Gold (dim_mahasiswa)      {gold_report['gold_count']}
Gold unique ID            {gold_report['unique_count']}
Gold with KHS             {gold_report['khs_coverage']}
Feature Store Training    {fs_report['training']}
Feature Store Inference   {fs_report['inference']}
""")

    # Validation checks
    gold_ok = gold_report['unique_count'] == 32703
    khs_ok = gold_report['khs_coverage'] == 28273
    train_ok = fs_report['training'] > 0
    inf_ok = fs_report['inference'] > 0

    print(f"Gold = 32703: {'PASS' if gold_ok else 'FAIL'} ({gold_report['unique_count']})")
    print(f"KHS = 28273:  {'PASS' if khs_ok else 'FAIL'} ({gold_report['khs_coverage']})")
    print(f"Training > 0: {'PASS' if train_ok else 'FAIL'} ({fs_report['training']})")
    print(f"Inference > 0: {'PASS' if inf_ok else 'FAIL'} ({fs_report['inference']})")

    all_pass = gold_ok and khs_ok and train_ok and inf_ok
    print(f"\nALL CHECKS: {'PASS' if all_pass else 'FAIL'}")
    print("\nPIPELINE FIX SELESAI")

if __name__ == "__main__":
    main()
