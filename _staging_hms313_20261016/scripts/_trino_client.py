"""Klien REST minimal untuk Trino (stdlib saja).

Dipakai oleh migrate_file_tables.py dan validate_tables.py agar bisa dibaca /
di-dry-run tanpa dependency Spark. Saat eksekusi nyata, jalankan di dalam
container yang punya akses ke Trino (mis. airflow-scheduler) atau host dengan
port 8082 terbuka.
"""
import json
import time
import urllib.request
import urllib.error


class TrinoError(RuntimeError):
    pass


class TrinoClient:
    def __init__(self, url="http://localhost:8082", user="staging", source="staging",
                 catalog="iceberg", schema="gold", timeout=180):
        self.url = url.rstrip("/")
        self.user = user
        self.source = source
        self.catalog = catalog
        self.schema = schema
        self.timeout = timeout

    def _headers(self):
        return {
            "X-Trino-User": self.user,
            "X-Trino-Source": self.source,
            "X-Trino-Catalog": self.catalog,
            "X-Trino-Schema": self.schema,
            "Content-Type": "text/plain; charset=utf-8",
        }

    def query(self, sql):
        req = urllib.request.Request(
            self.url + "/v1/statement",
            data=sql.encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        cols = None
        rows = []
        deadline = time.time() + self.timeout
        while True:
            if "error" in payload:
                msg = payload["error"].get("message", str(payload["error"]))
                raise TrinoError(msg)
            if cols is None and payload.get("columns"):
                cols = [c["name"] for c in payload["columns"]]
            rows.extend(payload.get("data", []))
            nxt = payload.get("nextUri")
            if not nxt:
                break
            if time.time() > deadline:
                raise TrinoError("timeout menunggu Trino selesai")
            time.sleep(0.4)
            req = urllib.request.Request(nxt, headers=self._headers())
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        return cols, rows

    def scalar(self, sql):
        _, rows = self.query(sql)
        return rows[0][0] if rows else None
