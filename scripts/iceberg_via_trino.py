import pandas as pd
import numpy as np
import requests
import time
from pathlib import Path

def execute_trino(sql):
    print("SQL (first 200 chars): " + sql[:200])
    response = requests.post(
        "http://trino:8082/v1/statement",
        headers={
            "X-Trino-User": "airflow",
            "X-Trino-Catalog": "iceberg",
            "X-Trino-Schema": "gold",
            "Content-Type": "application/json"
        },
        json={"query": sql},
        timeout=60
    )
    result = response.json()
    print("Response status:", response.status_code)
    print("Response keys:", list(result.keys()))
    next_uri = result.get("nextUri")
    
    while next_uri:
        time.sleep(1)
        resp = requests.get(next_uri, headers={"X-Trino-User": "airflow"}, timeout=60)
        result = resp.json()
        if result.get("data"):
            return result
        next_uri = result.get("nextUri")
    
    if result.get("error"):
        raise Exception("Trino error: " + str(result["error"]))
    return result

def main():
    print("Reading Excel...")
    df = pd.read_excel("/opt/airflow/data/data fix/inference_result_model_a_utama.xlsx")
    print("Loaded {} rows, {} columns".format(len(df), len(df.columns)))
    
    if "prediksi_label" in df.columns:
        df = df.drop(columns=["prediksi_label"])
    
    # Build column definitions
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
    
    # Create table - simple string concatenation
    create_sql = "CREATE TABLE IF NOT EXISTS iceberg.gold.inference_result_model_a_utama (" + cols_def + ") WITH (format = 'PARQUET', partitioning = ARRAY['angkatan'])"
    
    print("CREATE SQL: " + create_sql[:300])
    print("Creating table...")
    execute_trino(create_sql)
    print("Table created")
    
    # Insert data in batches
    batch_size = 500
    total = len(df)
    
    for start in range(0, total, 500):
        batch = df.iloc[start:start + 500]
        value_rows = []
        for _, row in batch.iterrows():
            vals = []
            for col in df.columns:
                v = row[col]
                if pd.isna(v):
                    vals.append("NULL")
                elif isinstance(v, bool):
                    vals.append("TRUE" if v else "FALSE")
                elif isinstance(v, (int, np.integer)):
                    vals.append(str(int(v)))
                elif isinstance(v, (float, np.floating)):
                    vals.append(str(float(v)))
                else:
                    escaped = str(v).replace("'", "''")
                    vals.append("'" + escaped + "'")
            value_rows.append("(" + ", ".join(vals) + ")")
        
        values_sql = ", ".join(value_rows)
        cols = ", ".join(df.columns)
        insert_sql = "INSERT INTO iceberg.gold.inference_result_model_a_utama (" + cols + ") VALUES " + values_sql
        
        execute_trino(insert_sql)
        print("Inserted batch: rows {} to {}".format(start, min(start+500, total)))
    
    # Verify
    result = execute_trino("SELECT COUNT(*) FROM iceberg.gold.inference_result_model_a_utama")
    print("Total rows in table: {}".format(result.get("data")))
    
    dist_result = execute_trino("SELECT prediksi, COUNT(*) as cnt FROM iceberg.gold.inference_result_model_a_utama GROUP BY prediksi")
    print("Distribution:")
    if dist_result and dist_result.get("data"):
        for row in dist_result["data"]:
            print("  prediksi={}: {}".format(row[0], row[1]))
    
    print("\nDone!")

if __name__ == "__main__":
    main()