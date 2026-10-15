import json
import http.cookiejar
import urllib.request

BASE = "http://localhost:8088"
TABLES = [
    "model_predictions_model_a",
    "prediction_by_angkatan_model_a",
    "model_metrics_model_a",
    "confusion_matrix_model_a",
    "classification_report_model_a",
    "training_label_distribution_model_a",
]

_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def req(method, path, token=None, payload=None, csrf=None):
    headers = {"Content-Type": "application/json", "Referer": BASE}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if csrf:
        headers["X-CSRFToken"] = csrf
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with _opener.open(r) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main():
    status, body = req(
        "POST", "/api/v1/security/login",
        payload={"username": "admin", "password": "change-me", "provider": "db", "refresh": True},
    )
    if status != 200:
        print("LOGIN FAILED", status, body)
        return
    token = body["access_token"]
    _, csrf = req("GET", "/api/v1/security/csrf_token/", token=token)
    csrf = csrf.get("result")

    existing, body = req("GET", "/api/v1/dataset/?q=(page_size:100)", token=token, csrf=csrf)
    have = {d["table_name"]: d["id"] for d in body.get("result", [])}

    for t in TABLES:
        if t in have:
            print(f"EXISTS {t} id={have[t]}")
            continue
        status, body = req(
            "POST", "/api/v1/dataset/", token=token, csrf=csrf,
            payload={"database": 1, "schema": "gold", "table_name": t},
        )
        if status in (200, 201):
            print(f"CREATED {t} id={body['id']}")
        else:
            print(f"FAILED {t} {status} {body}")


if __name__ == "__main__":
    main()
