"""
Register new tables in Superset as datasets via Superset REST API.
Usage: docker compose exec -T airflow-scheduler python /opt/airflow/scripts/register_superset_datasets.py
"""
import requests
import sys

BASE_URL = "http://superset:8088"  # Use Docker service name, not localhost

def login():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/v1/security/login", json={
        "username": "admin",
        "password": "change-me",
        "provider": "db"
    })
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text[:300]}")
        sys.exit(1)
    token = r.json()["access_token"]
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    r0 = s.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    if r0.status_code == 200:
        s.headers.update({
            "X-CSRFToken": r0.json()["result"],
            "Referer": BASE_URL
        })
    return s

def get_database_id(s, name="Academic Trino"):
    r = s.get(f"{BASE_URL}/api/v1/database/", params={"q": f"(filters:!((col:database_name,opr:eq,value:'{name}')))"})
    if r.status_code == 200:
        result = r.json().get("result", [])
        if result:
            return result[0]["id"]
    return None

def list_datasets(s):
    r = s.get(f"{BASE_URL}/api/v1/dataset/", params={"page_size": 100})
    if r.status_code == 200:
        return r.json().get("result", [])
    return []

def create_dataset(s, database_id, schema, table_name):
    payload = {
        "database": database_id,
        "schema": schema,
        "table_name": table_name,
    }
    r = s.post(f"{BASE_URL}/api/v1/dataset/", json=payload)
    return r.status_code, r.json() if r.status_code in [200, 201] else r.text[:300]

def main():
    s = login()
    db_id = get_database_id(s)
    if not db_id:
        print("ERROR: Could not find 'Academic Trino' database")
        sys.exit(1)
    print(f"Database ID: {db_id}")

    existing = list_datasets(s)
    existing_keys = {(d.get("schema"), d.get("table_name")) for d in existing}
    print(f"Existing datasets: {len(existing_keys)}")
    for schema, table in sorted(existing_keys):
        print(f"  {schema}.{table}")

    tables_to_register = [
        ("gold", "dim_mahasiswa"),
        ("gold", "fact_khs"),
        ("feature_store", "training_dataset"),
        ("feature_store", "inference_dataset"),
        ("feature_store", "prediction_result_without_smote"),
        ("feature_store", "prediction_result_with_smote"),
        ("feature_store", "prediction_comparison"),
    ]

    created = []
    skipped = []

    for schema, table in tables_to_register:
        key = (schema, table)
        if key in existing_keys:
            skipped.append(f"{schema}.{table}")
            continue

        status, resp = create_dataset(s, db_id, schema, table)
        if status in [200, 201]:
            ds_id = resp.get("id", "unknown")
            created.append(f"{schema}.{table} (id={ds_id})")
            print(f"  CREATED: {schema}.{table} -> id={ds_id}")
        else:
            print(f"  FAILED:  {schema}.{table} -> {resp}")

    print(f"\nSUMMARY:")
    print(f"  Created: {len(created)}")
    for c in created:
        print(f"    + {c}")
    print(f"  Skipped (already exist): {len(skipped)}")
    for sk in skipped:
        print(f"    - {sk}")

if __name__ == "__main__":
    main()
