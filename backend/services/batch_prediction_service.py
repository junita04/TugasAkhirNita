"""
Layanan prediksi batch untuk halaman Prediction.

Membaca file Excel yang diunggah, menghitung fitur dengan logika yang sama
dengan Gold/Feature Store (estimasi_semester & persentase_sks), lalu
memprediksi status kelulusan (Tepat Waktu / Terlambat) memakai model
Gaussian Naive Bayes yang SUDAH ada. Proses training dan model Machine
Learning TIDAK diubah.
"""

import math
from datetime import date
from pathlib import Path

import pandas as pd

from backend.spark.session import get_spark
from backend.utils.logger import get_logger

logger = get_logger(__name__)

UPLOAD_DIR = Path("data")

# Nama sheet pada file Excel template
MAHASISWA_SHEET = "Data Referensi Mahasiswa"
KURIKULUM_SHEET = "Data Kurikulum"

# Pemetaan kolom Excel -> kolom internal
MAHASISWA_COLUMNS = {
    "Jenis Kelamin": "jenis_kelamin",
    "Tanggal Masuk": "tanggal_masuk",
    "Tanggal Keluar": "tanggal_keluar",
    "IPK": "ipk",
    "Total SKS": "total_sks",
    "Jumlah MK": "jumlah_mk",
    "Status Mahasiswa": "status_mahasiswa",
}
KURIKULUM_COLUMNS = {
    "Nama Kurikulum": "nama_kurikulum",
    "Jumlah SKS Total": "jumlah_sks_total",
}

MODEL_PATH = Path("models") / "gaussian_nb"


def _model_exists() -> bool:
    if not MODEL_PATH.exists():
        return False
    if (MODEL_PATH / "_SUCCESS").exists():
        return True
    return any(MODEL_PATH.rglob("*"))


def _months_between(end_date, start_date):
    """Mendekati logika Spark months_between: tahun*12 + bulan + fraksi hari/31."""
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day >= start_date.day:
        months += (end_date.day - start_date.day) / 31.0
    else:
        months -= (start_date.day - end_date.day) / 31.0
    return months


def _to_date(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def _read_curriculum_sks(excel):
    """Membaca jumlah SKS kurikulum (baris pertama) dari sheet Data Kurikulum."""
    if KURIKULUM_SHEET not in excel.sheet_names:
        return None
    df = pd.read_excel(excel, sheet_name=KURIKULUM_SHEET)
    df = df.rename(columns=KURIKULUM_COLUMNS)
    if "jumlah_sks_total" not in df.columns or df.empty:
        return None
    value = df["jumlah_sks_total"].dropna().iloc[0]
    return float(value)


def compute_features(excel_file: Path) -> tuple[list[dict], int | None]:
    """
    Membaca Excel dan menghitung fitur prediksi per mahasiswa.

    Returns
    -------
    (rows, jumlah_sks_kurikulum)
        rows: daftar dict dengan fitur jenis_kelamin, estimasi_semester,
        ipk, total_sks, jumlah_mk, persentase_sks.
    """
    excel = pd.ExcelFile(excel_file)

    if MAHASISWA_SHEET not in excel.sheet_names:
        raise ValueError(f"Sheet '{MAHASISWA_SHEET}' tidak ditemukan.")

    df = pd.read_excel(excel, sheet_name=MAHASISWA_SHEET)
    df = df.rename(columns=MAHASISWA_COLUMNS)

    kurikulum_sks = _read_curriculum_sks(excel)

    rows = []
    today = date.today()

    for _, record in df.iterrows():
        jenis_kelamin = str(record.get("jenis_kelamin", "")).strip().upper()[:1]
        if jenis_kelamin not in ("L", "P"):
            continue

        tanggal_masuk = _to_date(record.get("tanggal_masuk"))
        if tanggal_masuk is None:
            continue
        tanggal_keluar = _to_date(record.get("tanggal_keluar")) or today

        lama_studi_bulan = math.ceil(_months_between(tanggal_keluar, tanggal_masuk))
        estimasi_semester = math.ceil(lama_studi_bulan / 6)

        ipk = record.get("ipk")
        total_sks = record.get("total_sks")
        jumlah_mk = record.get("jumlah_mk")
        if any(v is None for v in (ipk, total_sks, jumlah_mk)):
            continue

        ipk = float(ipk)
        total_sks = float(total_sks)
        jumlah_mk = float(jumlah_mk)

        persentase_sks = (
            (total_sks / kurikulum_sks) * 100 if kurikulum_sks else 0.0
        )

        rows.append({
            "jenis_kelamin": jenis_kelamin,
            "estimasi_semester": int(estimasi_semester),
            "ipk": ipk,
            "total_sks": int(total_sks),
            "jumlah_mk": int(jumlah_mk),
            "persentase_sks": round(persentase_sks, 4),
        })

    return rows, kurikulum_sks


def _fallback_prediction(rows: list[dict]) -> list[dict]:
    """Estimasi sementara bila model belum tersedia (tidak melatih ulang)."""
    results = []
    for row in rows:
        prediction = (
            "Tepat Waktu" if row["estimasi_semester"] <= 8 else "Terlambat"
        )
        results.append({
            **row,
            "prediction": prediction,
            "probability_tepat": None,
            "probability_terlambat": None,
        })
    return results


def predict_dataset(filename: str) -> dict:
    """
    Menjalankan prediksi batch terhadap file Excel yang sudah diunggah.

    Returns
    -------
    dict
        status, file, model_available, total, tepat_waktu, terlambat,
        dan rows (per-mahasiswa: fitur + prediction + probabilitas).
    """
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {filename}")

    rows, _ = compute_features(file_path)
    if not rows:
        return {
            "status": "success",
            "file": filename,
            "model_available": False,
            "total": 0,
            "tepat_waktu": 0,
            "terlambat": 0,
            "rows": [],
        }

    model_available = _model_exists()

    if not model_available:
        logger.warning("Model belum dilatih; memakai estimasi fallback.")
        results = _fallback_prediction(rows)
    else:
        try:
            results = _predict_with_model(rows)
        except Exception as exc:
            logger.warning(f"Prediksi dengan model gagal, memakai estimasi fallback: {exc}")
            model_available = False
            results = _fallback_prediction(rows)

    tepat = sum(1 for r in results if r["prediction"] == "Tepat Waktu")
    terlambat = sum(1 for r in results if r["prediction"] == "Terlambat")

    return {
        "status": "success",
        "file": filename,
        "model_available": model_available,
        "total": len(results),
        "tepat_waktu": tepat,
        "terlambat": terlambat,
        "rows": results,
    }


def _predict_with_model(rows: list[dict]) -> list[dict]:
    """Prediksi batch menggunakan model yang sudah ada di Model Registry."""
    from pyspark.ml.feature import StringIndexer, VectorAssembler
    from pyspark.sql.types import (
        DoubleType,
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    spark = get_spark("Batch Prediction")

    schema = StructType([
        StructField("jenis_kelamin", StringType(), True),
        StructField("estimasi_semester", IntegerType(), True),
        StructField("ipk", DoubleType(), True),
        StructField("total_sks", IntegerType(), True),
        StructField("jumlah_mk", IntegerType(), True),
        StructField("persentase_sks", DoubleType(), True),
    ])

    data = [
        (
            row["jenis_kelamin"],
            int(row["estimasi_semester"]),
            float(row["ipk"]),
            int(row["total_sks"]),
            int(row["jumlah_mk"]),
            float(row["persentase_sks"]),
        )
        for row in rows
    ]

    df = spark.createDataFrame(data, schema)

    gender_indexer = StringIndexer(
        inputCol="jenis_kelamin",
        outputCol="jenis_kelamin_index",
        handleInvalid="keep",
    )
    assembler = VectorAssembler(
        inputCols=[
            "jenis_kelamin_index",
            "estimasi_semester",
            "ipk",
            "total_sks",
            "jumlah_mk",
            "persentase_sks",
        ],
        outputCol="features",
    )
    from pyspark.ml import Pipeline
    feature_df = Pipeline(stages=[gender_indexer, assembler]).fit(df).transform(df)

    from backend.ml.predict import load_model
    model = load_model()

    prediction_df = model.transform(feature_df).select(
        "prediction", "probability"
    ).collect()

    labels = _resolve_label_order()

    results = []
    for row, prediction_row in zip(rows, prediction_df):
        prediction_idx = int(prediction_row["prediction"])
        probabilities = list(prediction_row["probability"])

        prediction_label = (
            labels[prediction_idx] if prediction_idx < len(labels) else "Terlambat"
        )

        prob_tepat = 0.0
        prob_terlambat = 0.0
        for idx, label in enumerate(labels):
            prob = probabilities[idx] if idx < len(probabilities) else 0.0
            if label == "Tepat Waktu":
                prob_tepat = float(prob)
            elif label == "Terlambat":
                prob_terlambat = float(prob)

        results.append({
            **row,
            "prediction": prediction_label,
            "probability_tepat": prob_tepat,
            "probability_terlambat": prob_terlambat,
        })

    return results


def _resolve_label_order() -> list[str]:
    """Urutan label sesuai StringIndexer saat training (fallback statis)."""
    from backend.services.prediction_service import _resolve_label_order as resolve

    try:
        return resolve()
    except Exception:
        return ["Tepat Waktu", "Terlambat"]
