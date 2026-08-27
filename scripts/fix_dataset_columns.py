"""
FIX: Refresh dataset column metadata.
All datasets show cols=0 which means columns were never fetched from Trino.
This causes all charts to fail with "no chart definition".
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
    print("FIXING DATASET COLUMNS")
    print("=" * 70)
    
    # Get all datasets
    r = s.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:100)")
    datasets = r.json()["result"]
    
    print(f"\nFound {len(datasets)} datasets")
    
    # For each dataset, try to refresh its columns
    for ds in datasets:
        ds_id = ds["id"]
        ds_name = ds["table_name"]
        ds_schema = ds.get("schema", "")
        
        print(f"\n--- Dataset {ds_id}: {ds_schema}.{ds_name} ---")
        
        # Method 1: PUT with existing data to trigger refresh
        # First get current dataset detail
        r2 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r2.status_code != 200:
            print(f"  Cannot get dataset: {r2.status_code}")
            continue
        
        detail = r2.json()["result"]
        current_cols = detail.get("columns", [])
        print(f"  Current columns: {len(current_cols)}")
        
        # Method 2: Try to update the dataset to trigger column fetch
        # Send the same data back - this might trigger a metadata refresh
        update_data = {
            "table_name": ds_name,
            "schema": ds_schema,
        }
        
        r3 = s.put(f"{BASE_URL}/api/v1/dataset/{ds_id}", json=update_data)
        print(f"  PUT update: status={r3.status_code}")
        if r3.status_code != 200:
            print(f"  Error: {r3.text[:200]}")
        
        time.sleep(0.5)
        
        # Check columns again
        r4 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r4.status_code == 200:
            new_cols = r4.json()["result"].get("columns", [])
            print(f"  Columns after refresh: {len(new_cols)}")
            if new_cols:
                col_names = [c["column_name"] for c in new_cols]
                print(f"  Column names: {col_names}")
    
    # Check if there's a specific refresh endpoint
    print("\n--- Checking refresh endpoints ---")
    
    # Try POST to dataset refresh
    for ds in datasets:
        ds_id = ds["id"]
        
        # Try /api/v1/dataset/{id}/refresh
        r5 = s.put(f"{BASE_URL}/api/v1/dataset/{ds_id}/refresh", json={})
        print(f"  PUT /dataset/{ds_id}/refresh: status={r5.status_code}")
        if r5.status_code == 200:
            # Check columns
            r6 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
            cols = r6.json()["result"].get("columns", [])
            print(f"    Columns: {len(cols)}")
            break
        elif r5.status_code == 404:
            print(f"    Not found")
            break
    
    # Try different refresh approach
    print("\n--- Alternative refresh approach ---")
    for ds in datasets[:3]:
        ds_id = ds["id"]
        
        # Try the legacy explore endpoint
        r7 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}/related/owners")
        print(f"  GET /dataset/{ds_id}/related/owners: status={r7.status_code}")

if __name__ == "__main__":
    main()
