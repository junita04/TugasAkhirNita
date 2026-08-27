"""
STEP 3 + 12: Validate datasets via SQL through Trino
"""
import requests
import json

TRINO_URL = "http://trino:8082/v1/statement"

def trino_query(sql):
    r = requests.post(TRINO_URL, data=sql, headers={
        "X-Trino-User": "academic",
        "X-Trino-Catalog": "iceberg",
        "Content-Type": "text/plain",
    })
    data = r.json()
    columns = [c["name"] for c in data.get("columns", [])]
    rows = data.get("data", [])
    return columns, rows

def main():
    print("=" * 80)
    print("STEP 3+12: VALIDATE DATASETS VIA SQL (Trino)")
    print("=" * 80)
    
    datasets = [
        ("gold", "data_referensi_mahasiswa"),
        ("gold", "model_metrics"),
        ("gold", "model_predictions"),
        ("gold", "prediction_by_angkatan"),
        ("gold", "confusion_matrix"),
        ("gold", "classification_report"),
    ]
    
    for schema, table in datasets:
        sql = f"SELECT COUNT(*) as cnt FROM iceberg.{schema}.{table}"
        cols, rows = trino_query(sql)
        count = rows[0][0] if rows else 0
        status = "OK" if count > 0 else "EMPTY!"
        print(f"  {schema}.{table:35s}: {count:>8,} rows  [{status}]")
    
    # Check 3 target students
    print("\n--- TARGET STUDENTS (MHS000063, MHS000361, MHS024954) ---")
    sql = """
    SELECT nim, nama_mahasiswa, status_mahasiswa, tanggal_keluar
    FROM iceberg.gold.data_referensi_mahasiswa
    WHERE nim IN ('MHS000063', 'MHS000361', 'MHS024954')
    ORDER BY nim
    """
    cols, rows = trino_query(sql)
    for row in rows:
        print(f"  {row[0]} | {row[1]:30s} | Status={row[2]} | Tgl Keluar={row[3]}")
    
    # Check model_predictions columns
    print("\n--- MODEL_PREDICTIONS COLUMNS ---")
    sql = "SELECT * FROM iceberg.gold.model_predictions LIMIT 1"
    cols, rows = trino_query(sql)
    print(f"  Columns: {cols}")
    
    # Check data_referensi_mahasiswa columns
    print("\n--- DATA_REFERENSI_MAHASISWA COLUMNS ---")
    sql = "SELECT * FROM iceberg.gold.data_referensi_mahasiswa LIMIT 1"
    cols, rows = trino_query(sql)
    print(f"  Columns: {cols}")

    # Check prediction_by_angkatan
    print("\n--- PREDICTION_BY_ANGKATAN DATA ---")
    sql = "SELECT * FROM iceberg.gold.prediction_by_angkatan ORDER BY angkatan"
    cols, rows = trino_query(sql)
    for row in rows:
        print(f"  {row}")
    
    # Check confusion_matrix
    print("\n--- CONFUSION_MATRIX DATA ---")
    sql = "SELECT * FROM iceberg.gold.confusion_matrix ORDER BY actual, predicted"
    cols, rows = trino_query(sql)
    for row in rows:
        print(f"  {row}")
    
    # Check classification_report
    print("\n--- CLASSIFICATION_REPORT DATA ---")
    sql = "SELECT * FROM iceberg.gold.classification_report ORDER BY class"
    cols, rows = trino_query(sql)
    for row in rows:
        print(f"  {row}")
    
    # Check model_metrics
    print("\n--- MODEL_METRICS DATA ---")
    sql = "SELECT * FROM iceberg.gold.model_metrics"
    cols, rows = trino_query(sql)
    for row in rows:
        print(f"  {row}")

if __name__ == "__main__":
    main()
