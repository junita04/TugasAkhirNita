"""
SMOKE TEST v4.0.0 — Validasi menyeluruh pipeline setelah perbaikan 8 fitur.

Jalankan dari container airflow-scheduler:
  docker compose exec airflow-scheduler python /opt/airflow/scripts/smoke_test_v4.py

Atau dari host:
  docker compose exec airflow-scheduler python /opt/airflow/scripts/smoke_test_v4.py
"""

import sys
import os

sys.path.insert(0, "/opt/airflow")
os.chdir("/opt/airflow")


def main():
    print("=" * 88)
    print("SMOKE TEST v4.0.0 — PIPELINE VALIDATION")
    print("=" * 88)

    errors = []

    # =========================================================
    # 1. GOLD LAYER VALIDATION
    # =========================================================
    print()
    print("# 1. GOLD LAYER VALIDATION")
    print("-" * 40)

    try:
        from backend.spark.session import get_spark
        from backend.config.settings import ICEBERG_NAMESPACE

        spark = get_spark("SmokeTest v4")

        # Check dim_mahasiswa schema
        dim = spark.table(f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa")
        dim_cols = set(dim.columns)
        dim_count = dim.count()

        required_dim = [
            "id_mahasiswa", "jenis_kelamin", "tanggal_masuk", "tanggal_keluar",
            "ipk", "total_sks", "jumlah_mk", "status_mahasiswa",
            "angkatan", "semester", "ip", "sks_seharusnya", "selisih_sks",
            "lama_studi", "status_kelulusan", "label",
        ]
        missing_dim = [c for c in required_dim if c not in dim_cols]

        print(f"  dim_mahasiswa rows    : {dim_count}")
        print(f"  dim_mahasiswa columns : {len(dim_cols)}")
        print(f"  required columns      : {len(required_dim)}")
        print(f"  missing columns       : {missing_dim if missing_dim else 'none'}")
        print(f"  SCHEMA CHECK          : {'PASS' if not missing_dim else 'FAIL'}")

        if missing_dim:
            errors.append(f"Gold dim_mahasiswa missing columns: {missing_dim}")

        # Check fact_khs schema
        fact = spark.table(f"{ICEBERG_NAMESPACE}.gold.fact_khs")
        fact_cols = set(fact.columns)
        fact_count = fact.count()

        required_fact = ["id_mahasiswa", "ip", "sks", "jumlah_data_khs"]
        missing_fact = [c for c in required_fact if c not in fact_cols]

        print(f"  fact_khs rows         : {fact_count}")
        print(f"  fact_khs columns      : {len(fact_cols)}")
        print(f"  missing fact columns  : {missing_fact if missing_fact else 'none'}")
        print(f"  FACT SCHEMA CHECK     : {'PASS' if not missing_fact else 'FAIL'}")

        if missing_fact:
            errors.append(f"Gold fact_khs missing columns: {missing_fact}")

        # Label distribution
        from pyspark.sql import functions as F
        label_dist = dim.groupBy("label").count().collect()
        print(f"  Label distribution:")
        for row in label_dist:
            print(f"    label={row['label']}: {row['count']}")

        status_dist = dim.groupBy("status_kelulusan").count().collect()
        print(f"  Status kelulusan distribution:")
        for row in status_dist:
            print(f"    {row['status_kelulusan']}: {row['count']}")

        # Angkatan distribution
        ang_dist = dim.groupBy("angkatan").count().orderBy("angkatan").collect()
        print(f"  Angkatan distribution:")
        for row in ang_dist:
            print(f"    {row['angkatan']}: {row['count']}")

    except Exception as e:
        print(f"  GOLD VALIDATION ERROR: {e}")
        errors.append(f"Gold validation: {e}")

    # =========================================================
    # 2. FEATURE STORE VALIDATION
    # =========================================================
    print()
    print("# 2. FEATURE STORE VALIDATION")
    print("-" * 40)

    try:
        from backend.feature_store.feature_engineering import FEATURE_X, FORBIDDEN_FEATURES

        expected_features = [
            "jk_enc", "angkatan", "ip", "ipk", "total_sks",
            "jumlah_mk", "sks_seharusnya", "selisih_sks",
        ]

        print(f"  FEATURE_X             : {FEATURE_X}")
        print(f"  Expected              : {expected_features}")
        print(f"  Feature count         : {len(FEATURE_X)}")
        print(f"  Feature match         : {'PASS' if FEATURE_X == expected_features else 'FAIL'}")
        print(f"  FORBIDDEN_FEATURES    : {FORBIDDEN_FEATURES}")

        if FEATURE_X != expected_features:
            errors.append(f"FEATURE_X mismatch: {FEATURE_X} vs {expected_features}")

        # Check training dataset
        training = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
        training_cols = sorted(training.columns)
        training_count = training.count()

        print(f"  Training rows         : {training_count}")
        print(f"  Training columns      : {training_cols}")

        # Check label column
        if "label" in training.columns:
            label_dist = training.groupBy("label").count().collect()
            print(f"  Training label dist:")
            for row in label_dist:
                print(f"    label={row['label']}: {row['count']}")
        else:
            print(f"  WARNING: 'label' column not in training dataset")
            errors.append("Training dataset missing 'label' column")

        # Check inference dataset
        inference = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")
        inference_cols = sorted(inference.columns)
        inference_count = inference.count()

        print(f"  Inference rows        : {inference_count}")
        print(f"  Inference columns     : {inference_cols}")

        # Check inference only has 2022-2024
        if "angkatan" in inference.columns:
            ang_dist = inference.groupBy("angkatan").count().orderBy("angkatan").collect()
            print(f"  Inference angkatan dist:")
            for row in ang_dist:
                print(f"    {row['angkatan']}: {row['count']}")
            invalid_angkatan = [row for row in ang_dist if row["angkatan"] not in [2022, 2023, 2024]]
            if invalid_angkatan:
                errors.append(f"Inference has non-2022-2024 angkatan: {[r['angkatan'] for r in invalid_angkatan]}")

    except Exception as e:
        print(f"  FEATURE STORE VALIDATION ERROR: {e}")
        errors.append(f"Feature store validation: {e}")

    # =========================================================
    # 3. SNAPSHOT 2026 VALIDATION
    # =========================================================
    print()
    print("# 3. SNAPSHOT 2026 VALIDATION")
    print("-" * 40)

    try:
        from backend.gold.gold_mahasiswa import TARGET_SKS, SNAPSHOT_SEMESTER

        print(f"  TARGET_SKS: {TARGET_SKS}")
        print(f"  SNAPSHOT_SEMESTER: {SNAPSHOT_SEMESTER}")

        expected_snapshot = {2022: 7, 2023: 5, 2024: 3}
        snapshot_ok = SNAPSHOT_SEMESTER == expected_snapshot
        print(f"  Snapshot match        : {'PASS' if snapshot_ok else 'FAIL'}")

        if not snapshot_ok:
            errors.append(f"SNAPSHOT_SEMESTER mismatch: {SNAPSHOT_SEMESTER} vs {expected_snapshot}")

        for angkatan, sem in sorted(SNAPSHOT_SEMESTER.items()):
            sks = TARGET_SKS[sem]
            print(f"  {angkatan} -> semester {sem} -> {sks} SKS")

        # Validate against inference data
        inference = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")
        if "sks_seharusnya" in inference.columns:
            sample = inference.select("angkatan", "sks_seharusnya").distinct().orderBy("angkatan").collect()
            print(f"  Inference sks_seharusnya:")
            for row in sample:
                print(f"    angkatan={row['angkatan']}: sks_seharusnya={row['sks_seharusnya']}")

    except Exception as e:
        print(f"  SNAPSHOT VALIDATION ERROR: {e}")
        errors.append(f"Snapshot validation: {e}")

    # =========================================================
    # 4. ML VALIDATION
    # =========================================================
    print()
    print("# 4. ML VALIDATION")
    print("-" * 40)

    try:
        from backend.ml.data_preparation import FEATURE_COLUMNS, TARGET_COLUMN, POSITIVE_CLASS

        expected_features = [
            "jk_enc", "angkatan", "ip", "ipk", "total_sks",
            "jumlah_mk", "sks_seharusnya", "selisih_sks",
        ]

        print(f"  FEATURE_COLUMNS      : {FEATURE_COLUMNS}")
        print(f"  TARGET_COLUMN         : {TARGET_COLUMN}")
        print(f"  POSITIVE_CLASS        : {POSITIVE_CLASS}")
        print(f"  Feature count         : {len(FEATURE_COLUMNS)}")
        print(f"  Feature match         : {'PASS' if FEATURE_COLUMNS == expected_features else 'FAIL'}")
        print(f"  Target is 'label'     : {'PASS' if TARGET_COLUMN == 'label' else 'FAIL'}")
        print(f"  Positive class = 1    : {'PASS' if POSITIVE_CLASS == 1 else 'FAIL'}")

        if FEATURE_COLUMNS != expected_features:
            errors.append(f"FEATURE_COLUMNS mismatch")
        if TARGET_COLUMN != "label":
            errors.append(f"TARGET_COLUMN should be 'label', got '{TARGET_COLUMN}'")
        if POSITIVE_CLASS != 1:
            errors.append(f"POSITIVE_CLASS should be 1, got {POSITIVE_CLASS}")

        # Check model registry path
        from backend.ml.registry import ARTIFACT_DIR, MODEL_VERSION
        print(f"  ARTIFACT_DIR          : {ARTIFACT_DIR}")
        print(f"  MODEL_VERSION         : {MODEL_VERSION}")

        expected_dir = os.path.join(os.path.dirname(ARTIFACT_DIR), "gaussian_nb_8_features")
        print(f"  Path contains 8_features : {'PASS' if '8_features' in ARTIFACT_DIR else 'FAIL'}")

        if "8_features" not in ARTIFACT_DIR:
            errors.append(f"ARTIFACT_DIR should contain '8_features': {ARTIFACT_DIR}")

    except Exception as e:
        print(f"  ML VALIDATION ERROR: {e}")
        errors.append(f"ML validation: {e}")

    # =========================================================
    # 5. SUMMARY
    # =========================================================
    print()
    print("=" * 88)
    print("SMOKE TEST SUMMARY")
    print("=" * 88)

    if errors:
        print(f"  STATUS: FAIL ({len(errors)} errors)")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
    else:
        print(f"  STATUS: PASS")

    print("=" * 88)

    return len(errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
