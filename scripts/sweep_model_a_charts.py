import json
import http.cookiejar
import urllib.request

BASE = "http://localhost:8088"

DASH3 = [74, 75, 77] + list(range(81, 90)) + [91, 100] + list(range(163, 173))
DASH6 = list(range(145, 173))
SLICES = sorted(set(DASH3 + DASH6))

_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def main():
    status, body = _req(
        "POST", "/api/v1/security/login",
        payload={"username": "admin", "password": "change-me", "provider": "db", "refresh": True},
    )
    if status != 200:
        print("LOGIN FAILED", status, body)
        return
    token = body["access_token"]

    ok, fail = 0, []
    for sid in SLICES:
        status, body = _req("GET", f"/api/v1/chart/{sid}/data/", token=token)
        rows = None
        if status == 200:
            res = body.get("result")
            if isinstance(res, list) and res:
                data = res[0].get("data")
                rows = len(data) if isinstance(data, list) else res[0].get("rowcount", "?")
            elif body.get("errors"):
                status = 500
        if status == 200:
            ok += 1
            print(f"OK   {sid} rows={rows}")
        else:
            fail.append(sid)
            msg = str(body)[:300]
            print(f"FAIL {sid} status={status} {msg}")
    print(f"\nTOTAL {len(SLICES)} ok={ok} fail={len(fail)} {fail}")


def _req(method, path, token=None, payload=None):
    import json as _json
    headers = {"Referer": BASE}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = _json.dumps(payload).encode() if payload is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with _opener.open(r, timeout=90) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


if __name__ == "__main__":
    main()
