import requests
import time

headers = {
    "X-Trino-User": "airflow",
    "X-Trino-Catalog": "hive_iceberg",
    "X-Trino-Schema": "gold",
    "Content-Type": "application/json"
}

def run_query(sql, desc):
    print(f"\n{desc}: {sql[:80]}...")
    result = requests.post("http://trino:8082/v1/statement", headers=headers, json={"query": sql}).json()
    print(f"  State: {result.get('stats', {}).get('state')}")
    next_uri = result.get("nextUri")
    while next_uri:
        time.sleep(1)
        r = requests.get(next_uri, headers=headers).json()
        if r.get("data"):
            print(f"  Data: {r['data']}")
        next_uri = r.get("nextUri")
    return result

# Count
run_query("SELECT COUNT(*) as cnt FROM hive_iceberg.gold.inference_result_model_utama", "Count")

# Distribution
run_query("""
    SELECT angkatan, prediksi_label, COUNT(*) as jumlah
    FROM hive_iceberg.gold.inference_result_model_utama
    GROUP BY angkatan, prediksi_label
    ORDER BY angkatan, prediksi_label
""", "Distribution per angkatan")

# Overall
run_query("""
    SELECT prediksi_label, COUNT(*) as jumlah
    FROM hive_iceberg.gold.inference_result_model_utama
    GROUP BY prediksi_label
""", "Overall distribution")