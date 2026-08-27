import requests, json

s = requests.Session()
r = s.post("http://localhost:8088/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
token = r.json()["access_token"]
s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})

r = s.get("http://localhost:8088/api/v1/chart/?q=(page_size:200)")
all_charts = r.json()["result"]

dashboard_charts = set(range(66, 92))
orphan_count = 0
for c in all_charts:
    cid = c["id"]
    if cid not in dashboard_charts:
        s.delete(f"http://localhost:8088/api/v1/chart/{cid}")
        name = c.get("slice_name", "?")
        print(f"Deleted orphan chart {cid}: {name}")
        orphan_count += 1

print(f"Cleaned {orphan_count} orphan charts")
print(f"Total charts remaining: {len(all_charts) - orphan_count}")
