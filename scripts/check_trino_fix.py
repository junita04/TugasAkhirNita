"""Check Trino connectivity for _fix tables."""
import requests
import json
import time

TRINO = "http://localhost:8082"
headers = {"X-Trino-User": "trino", "X-Trino-Catalog": "iceberg"}

def trino_query(sql):
    """Execute Trino query with async polling."""
    r = requests.post(f"{TRINO}/v1/statement", headers=headers, data=sql.encode("utf-8"))
    info = r.json()
    state = info.get("stats", {}).get("state", "UNKNOWN")
    uri = info.get("nextUri")
    
    while state != "FINISHED" and uri:
        time.sleep(2)
        r = requests.get(uri, headers=headers)
        info = r.json()
        state = info.get("stats", {}).get("state", "UNKNOWN")
        uri = info.get("nextUri")
        if info.get("error"):
            return {"error": info["error"].get("message", str(info["error"]))}
    
    columns = [c["name"] for c in info.get("columns", [])]
    rows = [row for row in info.get("data", [])]
    return {"columns": columns, "rows": rows, "state": state}

print("Checking Trino _fix tables...")

# List all tables in iceberg catalog
result = trino_query("SHOW SCHEMAS IN iceberg")
if "error" in result:
    print(f"Error: {result['error']}")
else:
    schemas = [r[0] for r in result["rows"]]
    print(f"Schemas: {schemas}")
    
    for schema in schemas:
        result2 = trino_query(f"SHOW TABLES IN iceberg.{schema}")
        if "error" in result2:
            print(f"  Error listing {schema}: {result2['error']}")
        else:
            tables = [r[0] for r in result2["rows"]]
            print(f"\n--- {schema} ---")
            for t in tables:
                print(f"  {t}")
                # Try to count
                result3 = trino_query(f"SELECT COUNT(*) FROM iceberg.{schema}.{t}")
                if "error" in result3:
                    print(f"    Error: {result3['error'][:100]}")
                else:
                    print(f"    Count: {result3['rows'][0][0]}")
