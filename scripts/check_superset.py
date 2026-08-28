import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
login_data = json.dumps({"username": "admin", "password": "change-me"}).encode()
req = urllib.request.Request(
    "http://superset:8088/api/v1/security/login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)
resp = opener.open(req)
token = json.loads(resp.read())["access_token"]

def api_get(path):
    req = urllib.request.Request(
        f"http://superset:8088{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return json.loads(opener.open(req).read())

# Dashboard info
d = api_get("/api/v1/dashboard/3")
r = d.get("result", {})
print(f"Dashboard: {r.get('dashboard_title', 'N/A')}")

# Gold datasets
ds = api_get("/api/v1/dataset/?q=(page_size:50)")
print("\nGold datasets:")
for x in ds.get("result", []):
    if "gold" in x.get("schema", ""):
        print(f"  id={x['id']} {x['schema']}.{x['table_name']}")

# Count charts
slc = api_get("/api/v1/chart/?q=(page_size:100)")
charts = slc.get("result", [])
print(f"\nTotal charts: {len(charts)}")
for c in charts:
    print(f"  id={c['id']} {c['slice_name']} type={c.get('viz_type','?')}")
