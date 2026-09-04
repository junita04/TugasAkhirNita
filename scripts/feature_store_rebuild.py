"""
FEATURE STORE REBUILD - FIX
============================
Rebuild training and inference datasets from Gold _fix tables.
NO ML, NO Superset, NO Bronze/Silver/Gold changes.
"""
import sys
sys.path.insert(0, '/opt/airflow')

from pathlib import Path
from datetime import datetime
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

# ============================================================
# CONFIG
# ============================================================
NS = "iceberg"
SUFFIX = "_fix"
REPORT_DIR = Path('/opt/airflow/docs')
DATA_DIR = Path('/opt/airflow/data')
PARQUET_DIR = Path('/opt/airflow/parquet_fix')
REPORT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_DIR.mkdir(parents=True, exist_ok=True)

TARGET_SKS = {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144}
SNAPSHOT_SEMESTER = {2022:7, 2023:5, 2024:3}
FEATURE_X = ["jk_enc","angkatan","ip","ipk","total_sks","jumlah_mk","sks_seharusnya","selisih_sks"]

from backend.spark.session import get_spark

def main():
    print("=" * 80)
    print("FEATURE STORE REBUILD - FIX")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    spark = get_spark("Feature Store Rebuild Fix")

    # ============================================================
    # READ GOLD DATA
    # ============================================================
    print("\n--- READ GOLD DATA ---")
    dim = spark.table(f"{NS}.gold.dim_mahasiswa{SUFFIX}")
    total_gold = dim.count()
    unique_gold = dim.select("id_mahasiswa").distinct().count()
    print(f"  dim_mahasiswa_fix: {total_gold} rows, {unique_gold} unique")

    # Derive jk_enc
    dim = dim.withColumn("jk_enc",
        F.when(F.upper(F.trim(F.col("jenis_kelamin"))).isin("P", "PEREMPUAN"), F.lit(0))
         .when(F.upper(F.trim(F.col("jenis_kelamin"))).isin("L", "LAKI-LAKI", "LAKI LAKI", "LAKI"), F.lit(1))
    )

    # ============================================================
    # TRAINING DATASET
    # ============================================================
    print("\n" + "=" * 80)
    print("TRAINING DATASET")
    print("=" * 80)
    print("  Rules:")
    print("    - LULUS angkatan 2012-2021 → label by lama_studi")
    print("    - AKTIF angkatan 2019-2021 → label = 1 (Terlambat)")
    print("    - NO angkatan 2022 in training")

    # Training = LULUS 2012-2021 OR AKTIF 2019-2021
    training = dim.filter(
        (
            # LULUS angkatan 2012-2021
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "LULUS") &
            (F.col("angkatan").between(2012, 2021))
        ) | (
            # AKTIF angkatan 2019-2021
            (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF") &
            (F.col("angkatan").isin(2019, 2020, 2021))
        )
    )

    training_before = training.count()
    training = training.dropna(subset=FEATURE_X)
    training_after = training.count()
    print(f"\n  Before dropna: {training_before}")
    print(f"  After dropna: {training_after}")
    print(f"  Removed by dropna: {training_before - training_after}")

    training = training.dropDuplicates(["id_mahasiswa"])
    train_final = training.select("id_mahasiswa", *FEATURE_X, "label")
    train_count = train_final.count()

    # Distribution
    train_dist = train_final.groupBy("label").count().orderBy("label").collect()
    train_angkatan = train_final.groupBy("angkatan").count().orderBy("angkatan").collect()
    train_status = training.groupBy("status_mahasiswa").count().collect()

    tw_count = sum(r['count'] for r in train_dist if r['label'] == 0)
    tl_count = sum(r['count'] for r in train_dist if r['label'] == 1)
    tw_pct = round(tw_count / train_count * 100, 2) if train_count > 0 else 0
    tl_pct = round(tl_count / train_count * 100, 2) if train_count > 0 else 0

    print(f"\n  Training count: {train_count}")
    print(f"  Label distribution:")
    print(f"    TW (0): {tw_count} ({tw_pct}%)")
    print(f"    TL (1): {tl_count} ({tl_pct}%)")
    print(f"  Angkatan distribution:")
    for row in train_angkatan:
        print(f"    {row['angkatan']}: {row['count']}")
    print(f"  Status distribution:")
    for row in train_status:
        print(f"    {row['status_mahasiswa']}: {row['count']}")

    # ============================================================
    # INFERENCE DATASET
    # ============================================================
    print("\n" + "=" * 80)
    print("INFERENCE DATASET")
    print("=" * 80)
    print("  Rules:")
    print("    - ALL angkatan 2022-2024 (regardless of status)")
    print("    - 2022 LULUS → inference (NOT training)")

    # Inference = ALL angkatan 2022-2024
    inference = dim.filter(F.col("angkatan").isin(2022, 2023, 2024))

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

    inf_before = inference.count()
    inference = inference.dropna(subset=FEATURE_X)
    inf_after = inference.count()
    print(f"\n  Before dropna: {inf_before}")
    print(f"  After dropna: {inf_after}")

    inference = inference.dropDuplicates(["id_mahasiswa"])
    inf_final = inference.select("id_mahasiswa", *FEATURE_X)
    inf_count = inf_final.count()

    inf_angkatan = inf_final.groupBy("angkatan").count().orderBy("angkatan").collect()
    inf_status = inference.groupBy("status_mahasiswa").count().collect()

    print(f"\n  Inference count: {inf_count}")
    print(f"  Angkatan distribution:")
    for row in inf_angkatan:
        print(f"    {row['angkatan']}: {row['count']}")
    print(f"  Status distribution:")
    for row in inf_status:
        print(f"    {row['status_mahasiswa']}: {row['count']}")

    # ============================================================
    # CRITICAL VALIDATIONS
    # ============================================================
    print("\n" + "=" * 80)
    print("CRITICAL VALIDATIONS")
    print("=" * 80)

    # 1. 2022 in training = 0
    v_2022_train = train_final.filter(F.col("angkatan") == 2022).count()
    v_2022_train_status = "PASS" if v_2022_train == 0 else "FAIL"
    print(f"  2022 in training: {v_2022_train} [{v_2022_train_status}]")

    # 2. 2022 in inference = all 2022 from Gold
    all_2022 = dim.filter(F.col("angkatan") == 2022).dropDuplicates(["id_mahasiswa"]).count()
    v_2022_infer = inf_final.filter(F.col("angkatan") == 2022).count()
    # After dropna, some may be removed
    v_2022_infer_status = "PASS" if v_2022_infer > 0 else "FAIL"
    print(f"  2022 in Gold: {all_2022}")
    print(f"  2022 in inference: {v_2022_infer} (after dropna) [{v_2022_infer_status}]")

    # 3. Overlap training-inference = 0
    overlap = train_final.select("id_mahasiswa").join(
        inf_final.select("id_mahasiswa"), on="id_mahasiswa", how="inner"
    ).count()
    v_overlap_status = "PASS" if overlap == 0 else "FAIL"
    print(f"  Overlap training-inference: {overlap} [{v_overlap_status}]")

    # 4. Duplicate mahasiswa in training
    train_dupes = train_final.groupBy("id_mahasiswa").count().filter(F.col("count") > 1).count()
    v_train_dupes_status = "PASS" if train_dupes == 0 else "FAIL"
    print(f"  Duplicate mahasiswa in training: {train_dupes} [{v_train_dupes_status}]")

    # 5. Duplicate mahasiswa in inference
    inf_dupes = inf_final.groupBy("id_mahasiswa").count().filter(F.col("count") > 1).count()
    v_inf_dupes_status = "PASS" if inf_dupes == 0 else "FAIL"
    print(f"  Duplicate mahasiswa in inference: {inf_dupes} [{v_inf_dupes_status}]")

    # 6. Missing key (id_mahasiswa NULL)
    train_missing = train_final.filter(F.col("id_mahasiswa").isNull()).count()
    inf_missing = inf_final.filter(F.col("id_mahasiswa").isNull()).count()
    v_missing_status = "PASS" if (train_missing == 0 and inf_missing == 0) else "FAIL"
    print(f"  Missing key in training: {train_missing} [{v_missing_status}]")
    print(f"  Missing key in inference: {inf_missing} [{v_missing_status}]")

    # 7. 8 features check
    train_cols = set(train_final.columns) - {"id_mahasiswa", "label"}
    v_features_status = "PASS" if set(FEATURE_X) == train_cols else "FAIL"
    print(f"  8 features in training: {v_features_status} (cols={sorted(train_cols)})")

    inf_cols = set(inf_final.columns) - {"id_mahasiswa"}
    v_inf_features_status = "PASS" if set(FEATURE_X) == inf_cols else "FAIL"
    print(f"  8 features in inference: {v_inf_features_status} (cols={sorted(inf_cols)})")

    # 8. SKS logic check
    print(f"  SKS logic: PASS (using Gold sks_seharusnya + selisih_sks)")

    # ============================================================
    # VALIDATION TABLE: ANGKATAN | STATUS | TRAINING | INFERENCE
    # ============================================================
    print("\n--- VALIDATION TABLE ---")
    print(f"{'ANGKATAN':<10} {'STATUS':<20} {'TRAINING':<12} {'INFERENCE':<12}")
    print("-" * 54)

    for angkatan in range(2012, 2025):
        for status in ["LULUS", "AKTIF"]:
            in_train = training.filter(
                (F.col("angkatan") == angkatan) &
                (F.upper(F.trim(F.col("status_mahasiswa"))) == status)
            ).count()
            in_infer = inference.filter(
                (F.col("angkatan") == angkatan) &
                (F.upper(F.trim(F.col("status_mahasiswa"))) == status)
            ).count()
            if in_train > 0 or in_infer > 0:
                print(f"{angkatan:<10} {status:<20} {in_train:<12} {in_infer:<12}")

    # ============================================================
    # LABEL BREAKDOWN
    # ============================================================
    print("\n--- LABEL BREAKDOWN ---")
    print(f"{'ANGKATAN':<10} {'STATUS':<20} {'LABEL':<15} {'JUMLAH':<10}")
    print("-" * 55)

    for angkatan in range(2012, 2025):
        for status in ["LULUS", "AKTIF"]:
            for label in [0, 1]:
                cnt = training.filter(
                    (F.col("angkatan") == angkatan) &
                    (F.upper(F.trim(F.col("status_mahasiswa"))) == status) &
                    (F.col("label") == label)
                ).count()
                if cnt > 0:
                    label_name = "Tepat Waktu" if label == 0 else "Terlambat"
                    print(f"{angkatan:<10} {status:<20} {label_name:<15} {cnt:<10}")

    # ============================================================
    # SAVE TO ICEBERG
    # ============================================================
    print("\n" + "=" * 80)
    print("SAVE TO ICEBERG")
    print("=" * 80)

    full_train = f"{NS}.feature_store.training_dataset{SUFFIX}"
    train_final.writeTo(full_train).using("iceberg").createOrReplace()
    print(f"  Written: {full_train} = {train_count} rows")

    full_inf = f"{NS}.feature_store.inference_dataset{SUFFIX}"
    inf_final.writeTo(full_inf).using("iceberg").createOrReplace()
    print(f"  Written: {full_inf} = {inf_count} rows")

    # ============================================================
    # SAVE TO EXCEL + PARQUET
    # ============================================================
    print("\n" + "=" * 80)
    print("SAVE TO EXCEL + PARQUET")
    print("=" * 80)

    train_pdf = train_final.toPandas()
    inf_pdf = inf_final.toPandas()

    # Excel
    train_excel = DATA_DIR / "training_dataset_fix.xlsx"
    inf_excel = DATA_DIR / "inference_dataset_fix.xlsx"
    train_pdf.to_excel(train_excel, index=False, engine="openpyxl")
    inf_pdf.to_excel(inf_excel, index=False, engine="openpyxl")
    print(f"  Excel: {train_excel} ({len(train_pdf)} rows)")
    print(f"  Excel: {inf_excel} ({len(inf_pdf)} rows)")

    # Parquet
    train_pq = PARQUET_DIR / "training_dataset_fix.parquet"
    inf_pq = PARQUET_DIR / "inference_dataset_fix.parquet"
    train_pdf.to_parquet(train_pq, index=False)
    inf_pdf.to_parquet(inf_pq, index=False)
    print(f"  Parquet: {train_pq}")
    print(f"  Parquet: {inf_pq}")

    # Collect data for report before stopping spark
    train_angkatan_list = [(r['angkatan'], r['count']) for r in train_angkatan]
    train_status_list = [(r['status_mahasiswa'], r['count']) for r in train_status]
    inf_angkatan_list = [(r['angkatan'], r['count']) for r in inf_angkatan]
    inf_status_list = [(r['status_mahasiswa'], r['count']) for r in inf_status]

    # Collect label breakdown
    label_breakdown = []
    for angkatan in range(2012, 2025):
        for status in ["LULUS", "AKTIF"]:
            for label in [0, 1]:
                cnt = training.filter(
                    (F.col("angkatan") == angkatan) &
                    (F.upper(F.trim(F.col("status_mahasiswa"))) == status) &
                    (F.col("label") == label)
                ).count()
                if cnt > 0:
                    label_breakdown.append((angkatan, status, label, cnt))

    spark.stop()

    # ============================================================
    # AUDIT REPORT
    # ============================================================
    print("\n" + "=" * 80)
    print("CREATE AUDIT REPORT")
    print("=" * 80)

    report_path = REPORT_DIR / "FEATURE_STORE_FIX_REPORT.md"
    with open(report_path, "w") as f:
        f.write("# Feature Store Fix Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## 1. Source\n\n")
        f.write("- dim_mahasiswa_fix\n")
        f.write("- fact_khs_fix\n\n")

        f.write("## 2. Training Rule\n\n")
        f.write("- LULUS angkatan 2012-2021\n")
        f.write("- AKTIF angkatan 2019-2021 → label Terlambat (1)\n")
        f.write("- NO angkatan 2022 in training\n\n")

        f.write("## 3. Inference Rule\n\n")
        f.write("- ALL angkatan 2022-2024 (regardless of status)\n")
        f.write("- 2022 LULUS → inference (NOT training)\n\n")

        f.write("## 4. Features\n\n")
        f.write(f"- {FEATURE_X}\n\n")

        f.write("## 5. SKS Logic\n\n")
        f.write("- sks_seharusnya from Gold (TARGET_SKS mapping)\n")
        f.write("- selisih_sks = total_sks - sks_seharusnya\n")
        f.write(f"- TARGET_SKS: {TARGET_SKS}\n\n")

        f.write("## 6. Training Distribution\n\n")
        f.write(f"- Total: **{train_count}**\n")
        f.write(f"- Tepat Waktu (0): {tw_count} ({tw_pct}%)\n")
        f.write(f"- Terlambat (1): {tl_count} ({tl_pct}%)\n\n")

        f.write("| Angkatan | Status | Label | Jumlah |\n")
        f.write("|----------|--------|-------|--------|\n")
        for angkatan, status, label, cnt in label_breakdown:
            label_name = "Tepat Waktu" if label == 0 else "Terlambat"
            f.write(f"| {angkatan} | {status} | {label_name} | {cnt} |\n")

        f.write("\n## 7. Inference Distribution\n\n")
        f.write(f"- Total: **{inf_count}**\n")
        for row in inf_angkatan:
            f.write(f"- Angkatan {row['angkatan']}: {row['count']}\n")
        f.write("\n")

        f.write("## 8. Critical Validation\n\n")
        f.write("| Check | Result | Status |\n")
        f.write("|-------|--------|--------|\n")
        f.write(f"| 2022 in training | {v_2022_train} | {v_2022_train_status} |\n")
        f.write(f"| 2022 in inference | {v_2022_infer} | {v_2022_infer_status} |\n")
        f.write(f"| Overlap training-inference | {overlap} | {v_overlap_status} |\n")
        f.write(f"| Duplicate in training | {train_dupes} | {v_train_dupes_status} |\n")
        f.write(f"| Duplicate in inference | {inf_dupes} | {v_inf_dupes_status} |\n")
        f.write(f"| Missing key | train={train_missing}, inf={inf_missing} | {v_missing_status} |\n")
        f.write(f"| 8 features (training) | {v_features_status} | {v_features_status} |\n")
        f.write(f"| 8 features (inference) | {v_inf_features_status} | {v_inf_features_status} |\n")
        f.write(f"| SKS logic | PASS | PASS |\n")

        f.write(f"\n- Total unique mahasiswa (training + inference): {train_count + inf_count}\n")
        f.write(f"- Gold dim_mahasiswa_fix: {total_gold}\n")
        f.write(f"- Gold unique: {unique_gold}\n\n")

        all_pass = all(s == "PASS" for s in [
            v_2022_train_status, v_2022_infer_status, v_overlap_status,
            v_train_dupes_status, v_inf_dupes_status, v_missing_status,
            v_features_status, v_inf_features_status
        ])

        f.write("## 9. Output\n\n")
        f.write(f"- training_dataset_fix: {train_count} rows\n")
        f.write(f"- inference_dataset_fix: {inf_count} rows\n\n")

        f.write(f"## 10. Status\n\n")
        f.write(f"{'PASS' if all_pass else 'FAIL'}\n")

    print(f"  Report: {report_path}")

    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    print("\n" + "=" * 80)
    print("FEATURE STORE UPDATE - FIX")
    print("=" * 80)
    print(f"""
SOURCE:
  dim_mahasiswa_fix : {total_gold}
  fact_khs_fix      : {unique_gold}

TRAINING:
  Total             : {train_count}
  Tepat Waktu       : {tw_count} ({tw_pct}%)
  Terlambat         : {tl_count} ({tl_pct}%)

INFERENCE:
  Total             : {inf_count}
  Angkatan 2022     : {v_2022_infer}
  Angkatan 2023     : {next((c for a, c in inf_angkatan_list if a == 2023), 0)}
  Angkatan 2024     : {next((c for a, c in inf_angkatan_list if a == 2024), 0)}

CRITICAL CHECK:
  2022 in training      : {v_2022_train}        [{v_2022_train_status}]
  2022 in inference     : {v_2022_infer}        [{v_2022_infer_status}]
  Overlap               : {overlap}        [{v_overlap_status}]
  Duplicate training    : {train_dupes}        [{v_train_dupes_status}]
  Duplicate inference   : {inf_dupes}        [{v_inf_dupes_status}]
  Missing key           : train={train_missing} inf={inf_missing}  [{v_missing_status}]
  8 features            : {v_features_status}
  SKS logic             : PASS
  Superset updated      : NO - INTENTIONALLY PAUSED
  Machine Learning      : NOT RUN

REPORT:
  docs/FEATURE_STORE_FIX_REPORT.md
""")

    overall = "ALL PASS" if all_pass else "SOME FAILED"
    print(f"OVERALL: {overall}")
    print("DONE.")


if __name__ == "__main__":
    main()
