import pandas as pd
import numpy as np
import subprocess
import os
import tempfile
import shutil

TRINO_CONTAINER = "academic-datalakehouse-trino-1"
TABLE = "iceberg.gold.inference_result_model_a_utama"

def run_trino_sql_file(host_sql_path):
    """Copy SQL file to container and execute via --file"""
    container_path = "/tmp/exec.sql"
    # Copy file to container
    subprocess.run(["docker", "cp", host_sql_path, TRINO_CONTAINER + ":" + container_path], check=True, capture_output=True)
    # Execute
    cmd = [
        "docker", "exec", TRINO_CONTAINER,
        "trino", "--server", "trino:8082",
        "--catalog", "iceberg",
        "--schema", "gold",
        "--file", container_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    # Cleanup
    subprocess.run(["docker", "exec", TRINO_CONTAINER, "rm", "-f", container_path], capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        error_lines = [l for l in stderr.split('\n') if 'WARNING' not in l and 'Log logr' not in l and l.strip()]
        if error_lines:
            raise Exception("Trino error: " + '\n'.join(error_lines))
    return result.stdout.strip()

def run_trino_execute(sql):
    """Execute single SQL via --execute"""
    cmd = [
        "docker", "exec", TRINO_CONTAINER,
        "trino", "--server", "trino:8082",
        "--catalog", "iceberg",
        "--schema", "gold",
        "--execute", sql
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        error_lines = [l for l in stderr.split('\n') if 'WARNING' not in l and 'Log logr' not in l and l.strip()]
        if error_lines:
            raise Exception("Trino error: " + '\n'.join(error_lines))
    return result.stdout.strip()

def escape_sql_val(v):
    if pd.isna(v):
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return str(float(v))
    return "'" + str(v).replace("'", "''") + "'"

def main():
    print("=" * 60)
    print("Writing Inference Results to Iceberg via Trino CLI")
    print("=" * 60)

    df = pd.read_excel(r"D:\TA\TugasAkhirNita\Data\data fix\inference_result_model_a_utama.xlsx")
    print("Loaded {} rows, {} columns".format(len(df), len(df.columns)))
    print("Columns:", list(df.columns))

    if "prediksi_label" in df.columns:
        df = df.drop(columns=["prediksi_label"])

    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        if dtype == "int64":
            sql_type = "BIGINT"
        elif dtype == "float64":
            sql_type = "DOUBLE"
        elif dtype == "object":
            sql_type = "VARCHAR"
        else:
            sql_type = "VARCHAR"
        columns.append(col + " " + sql_type)

    cols_def = ", ".join(columns)

    print("Creating schema...")
    run_trino_execute("CREATE SCHEMA IF NOT EXISTS iceberg.gold")
    print("Creating table...")
    run_trino_execute("CREATE TABLE IF NOT EXISTS " + TABLE + " (" + cols_def + ") WITH (format = 'PARQUET')")
    print("Table created")

    # Check existing
    count_result = run_trino_execute("SELECT COUNT(*) FROM " + TABLE)
    existing = int(count_result.split('\n')[0].strip().strip('"'))
    print("Existing rows: {}".format(existing))

    if existing >= len(df):
        print("Table already has enough rows, skipping insert")
    else:
        if existing > 0:
            print("Truncating partial data...")
            run_trino_execute("DELETE FROM " + TABLE)

        batch_size = 500
        total = len(df)
        cols = ", ".join(df.columns)

        for start in range(0, total, batch_size):
            batch = df.iloc[start:start + batch_size]
            value_rows = []
            for _, row in batch.iterrows():
                vals = [escape_sql_val(row[col]) for col in df.columns]
                value_rows.append("(" + ", ".join(vals) + ")")

            values_sql = ", ".join(value_rows)
            insert_sql = "INSERT INTO " + TABLE + " (" + cols + ") VALUES " + values_sql + ";\n"

            # Write SQL file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as f:
                f.write(insert_sql)
                tmp_path = f.name

            try:
                run_trino_sql_file(tmp_path)
                print("Inserted batch: rows {} to {}".format(start, min(start + batch_size, total)))
            finally:
                os.unlink(tmp_path)

    # Verify
    count_result = run_trino_execute("SELECT COUNT(*) FROM " + TABLE)
    print("Total rows in table: {}".format(count_result))

    dist_result = run_trino_execute("SELECT prediksi, COUNT(*) as cnt FROM " + TABLE + " GROUP BY prediksi")
    print("Distribution:")
    for line in dist_result.split('\n'):
        if line.strip():
            print("  " + line)

    print("\nDone!")

if __name__ == "__main__":
    main()
