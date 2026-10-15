"""Retry register 9 tabel yang gagal pada restore_iceberg_all.py.

Penyebab:
  - 8 tabel: "More than one latest metadata file found" -> sebutkan
    metadata_file_name secara eksplisit (paling baru berdasarkan mtime/snapshot).
  - feature_store.inference_result_new: metadata menyatakan location
    s3a://.../feature_store.db/inference_result (bukan ..._new) -> daftarkan
    dengan table_location sesuai deklarasi metadata.

Verifikasi count(*) vs expected dari snapshot summary, lalu merge hasil
ke restore_report.json (register_failed -> registered, verify_failed -> verified).
"""
import json
import sys
from pathlib import Path

from restore_iceberg_all import TrinoError, trino_execute, qident

REPORT = Path(r"D:\TA\TugasAkhirNita\scripts\restore_report.json")

BASE = "s3://warehouse/iceberg"

RETRIES = [
    {
        "schema": "bronze", "table": "data_khs",
        "location": f"{BASE}/bronze.db/data_khs",
        "metadata_file_name": "00000-38cdeedc-4add-403c-91c7-5f4205a5dd10.metadata.json",
        "expected": 28473,
    },
    {
        "schema": "bronze", "table": "data_referensi_mahasiswa",
        "location": f"{BASE}/bronze.db/data_referensi_mahasiswa",
        "metadata_file_name": "00000-579a25b5-d45c-4b90-b740-92e83b8361ab.metadata.json",
        "expected": 37655,
    },
    {
        "schema": "feature_store", "table": "feature_store_graduation_prediction",
        "location": f"{BASE}/feature_store.db/feature_store_graduation_prediction",
        "metadata_file_name": "00000-0c483f19-04be-4269-b3be-af0fbac0c0f1.metadata.json",
        "expected": 13328,
    },
    {
        "schema": "feature_store", "table": "inference_mahasiswa_aktif",
        "location": f"{BASE}/feature_store.db/inference_mahasiswa_aktif",
        "metadata_file_name": "00000-b2cb8d94-fb1a-4593-93d3-48a33fa3ef71.metadata.json",
        "expected": 14662,
    },
    {
        "schema": "feature_store", "table": "training_kelulusan",
        "location": f"{BASE}/feature_store.db/training_kelulusan",
        "metadata_file_name": "00000-8f1ab441-a0c3-46af-9bae-4e4817918208.metadata.json",
        "expected": 13181,
    },
    {
        "schema": "gold", "table": "data_referensi_mahasiswa",
        "location": f"{BASE}/gold.db/data_referensi_mahasiswa",
        "metadata_file_name": "00000-62754705-6b96-49b3-9d70-d46bbe1caae7.metadata.json",
        "expected": 32712,
    },
    {
        "schema": "feature_store", "table": "prediction_result_with_smote",
        "location": f"{BASE}/feature_store.db/prediction_result_with_smote",
        "metadata_file_name": "00063-099d5882-99e8-4425-87b4-4eb0429a1324.metadata.json",
        "expected": 12501,
    },
    {
        "schema": "feature_store", "table": "prediction_result_without_smote",
        "location": f"{BASE}/feature_store.db/prediction_result_without_smote",
        "metadata_file_name": "00063-c0ed2509-9c72-4bc9-86cd-5ca6cf2108b8.metadata.json",
        "expected": 12501,
    },
    {
        "schema": "feature_store", "table": "inference_result_new",
        "location": f"{BASE}/feature_store.db/inference_result",
        "expected": 12338,
    },
]


def main():
    results = {"registered": [], "register_failed": [],
               "verified": [], "verify_failed": []}

    # Tabel yang sudah terdaftar (mis. setelah run sebagian) -> langsung verifikasi
    existing = set()
    for s in {e["schema"] for e in RETRIES}:
        for r in trino_execute(f"SHOW TABLES IN iceberg.{qident(s)}"):
            existing.add(f"{s}.{r[0]}")

    for e in RETRIES:
        full = f"{e['schema']}.{e['table']}"
        if full in existing:
            results["registered"].append(full)
            print(f"[reg]    SKIP (sudah ada) {full}")
            continue
        parts = [
            f"schema_name => '{e['schema']}'",
            f"table_name => '{e['table']}'",
            f"table_location => '{e['location']}'",
        ]
        if e.get("metadata_file_name"):
            parts.append(f"metadata_file_name => '{e['metadata_file_name']}'")
        sql = "CALL iceberg.system.register_table(" + ", ".join(parts) + ")"
        try:
            trino_execute(sql)
            results["registered"].append(full)
            print(f"[reg]    OK   {full}")
        except TrinoError as ex:
            results["register_failed"].append({"table": full, "error": str(ex)[:500]})
            print(f"[reg]    FAIL {full}: {str(ex)[:300]}")

    for e in RETRIES:
        full = f"{e['schema']}.{e['table']}"
        ident = f"{qident(e['schema'])}.{qident(e['table'])}"
        try:
            rows = trino_execute(f"SELECT count(*) FROM {ident}")
            cnt = int(rows[0][0])
            ok = cnt == e["expected"]
            entry = {"table": full, "rows": cnt, "expected": e["expected"],
                     "match": ok}
            (results["verified"] if ok else results["verify_failed"]).append(entry)
            print(f"[count]  {'OK  ' if ok else 'DIFF'} {full} = {cnt} (expected {e['expected']})")
        except TrinoError as ex:
            results["verify_failed"].append({"table": full, "error": str(ex)[:500]})
            print(f"[count]  FAIL {full}: {str(ex)[:300]}")

    # Merge ke laporan utama
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    failed_tables = set(results["registered"])
    report["register_failed"] = [r for r in report["register_failed"]
                                 if r["table"] not in failed_tables]
    report["registered"].extend(results["registered"])
    vf_tables = {r["table"] for r in results["verified"]}
    report["verify_failed"] = [r for r in report["verify_failed"]
                               if r["table"] not in vf_tables]
    report["verified"].extend(results["verified"])
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"Registered baru : {len(results['registered'])}")
    print(f"Register gagal  : {len(results['register_failed'])}")
    print(f"Verified OK     : {len(results['verified'])}")
    print(f"Verify DIFF     : {len(results['verify_failed'])}")
    print(f"Report sisa register_failed: {len(report['register_failed'])}, "
          f"verify_failed: {len(report['verify_failed'])}")

    if results["register_failed"] or results["verify_failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
