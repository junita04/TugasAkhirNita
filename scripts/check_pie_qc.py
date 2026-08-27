import requests, json

s = requests.Session()
r = s.post("http://localhost:8088/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
token = r.json()["access_token"]
s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})

for cid in [72, 73, 78, 88]:
    r = s.get(f"http://localhost:8088/api/v1/chart/{cid}")
    c = r.json()["result"]
    name = c["slice_name"]
    qc = json.loads(c["query_context"])
    q = qc["queries"][0]
    form = qc.get("form_data", {})

    print(f"Chart {cid}: {name}")
    print(f"  form_data.metric: {form.get('metric', 'MISSING')}")
    print(f"  form_data.metrics: {form.get('metrics', 'MISSING')}")
    print(f"  form_data.groupby: {form.get('groupby', 'MISSING')}")
    print(f"  QC queries[0].metrics: {q.get('metrics', [])}")
    print(f"  QC queries[0].columns: {q.get('columns', [])}")
    print()
