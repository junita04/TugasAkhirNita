"""
Refresh ALL dataset columns using the /refresh endpoint.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE_URL})
    return s

def main():
    s = api()
    
    print("=" * 70)
    print("REFRESH ALL DATASET COLUMNS")
    print("=" * 70)
    
    r = s.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:100)")
    datasets = r.json()["result"]
    
    # Only refresh valid datasets (those that exist in Trino)
    valid_schemas = {
        "data_referensi_mahasiswa": "gold",
        "model_metrics": "gold",
        "model_predictions": "gold",
        "prediction_by_angkatan": "gold",
        "confusion_matrix": "gold",
        "classification_report": "gold",
    }
    
    for ds in datasets:
        ds_id = ds["id"]
        ds_name = ds["table_name"]
        ds_schema = ds.get("schema", "")
        
        # Skip old/invalid datasets
        if ds_name not in valid_schemas:
            print(f"\nSkipping {ds_schema}.{ds_name} (not in valid set)")
            continue
        
        print(f"\n--- Refreshing {ds_schema}.{ds_name} (id={ds_id}) ---")
        
        # Refresh columns
        r2 = s.put(f"{BASE_URL}/api/v1/dataset/{ds_id}/refresh", json={})
        print(f"  Refresh: status={r2.status_code}")
        
        time.sleep(1)
        
        # Check columns
        r3 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r3.status_code == 200:
            detail = r3.json()["result"]
            cols = detail.get("columns", [])
            col_names = [c["column_name"] for c in cols]
            print(f"  Columns: {len(cols)} -> {col_names}")
    
    # Final verification
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)
    
    r4 = s.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:100)")
    all_ds = r4.json()["result"]
    
    for ds in all_ds:
        ds_id = ds["id"]
        ds_name = ds["table_name"]
        r5 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r5.status_code == 200:
            cols = r5.json()["result"].get("columns", [])
            status = "OK" if cols else "EMPTY"
            print(f"  {ds_name}: {len(cols)} columns [{status}]")

if __name__ == "__main__":
    main()
