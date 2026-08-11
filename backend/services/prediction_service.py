"""
Layanan prediksi untuk satu record mahasiswa.

Menggunakan model Gaussian Naive Bayes dari Model Registry (backend/ml/predict.py)
tanpa mengubah modul inti. Jika model belum tersedia, mengembalikan estimasi
sementara dengan fallback heuristik (tidak melatih ulang).
"""

from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE, MODEL_DIR
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = MODEL_DIR / "gaussian_nb"

FEATURE_COLUMNS = [
    "estimasi_semester",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "persentase_sks",
]

# urutan label saat training ditentukan oleh StringIndexer (default frequencyDesc).
# Disimpan sebagai cache agar tidak membaca tabel berulang kali.
_label_cache = {"labels": None, "ts": 0.0}


def _model_exists() -> bool:
    if not MODEL_PATH.exists():
        return False
    if (MODEL_PATH / "_SUCCESS").exists():
        return True
    return any(MODEL_PATH.rglob("*"))


def _resolve_label_order():
    """
    Mengembalikan urutan label sesuai StringIndexer pada saat training:
    diurutkan berdasarkan frekuensi menurun pada status_kelulusan.
    Fallback ke urutan statis bila tabel training tidak dapat dibaca.
    """
    import time

    cached = _label_cache["labels"]
    if cached is not None and (time.time() - _label_cache["ts"]) < 300:
        return cached

    labels = ["Tepat Waktu", "Terlambat"]
    try:
        spark = get_spark("Label Order")
        df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
        if "status_kelulusan" in df.columns:
            counts = [
                (str(r[0]), r[1])
                for r in df.groupBy("status_kelulusan").count().collect()
                if r[0] is not None
            ]
            if counts:
                labels = [label for label, _ in sorted(
                    counts, key=lambda item: item[1], reverse=True
                )]
        _label_cache["labels"] = labels
        _label_cache["ts"] = time.time()
    except Exception as exc:
        logger.warning(f"Gagal membaca urutan label dari training dataset: {exc}")

    return labels


def _build_input_frame(spark, payload: dict):
    schema = StructType([
        StructField("jenis_kelamin", StringType(), True),
        StructField("estimasi_semester", IntegerType(), True),
        StructField("ipk", DoubleType(), True),
        StructField("total_sks", IntegerType(), True),
        StructField("jumlah_mk", IntegerType(), True),
        StructField("persentase_sks", DoubleType(), True),
    ])

    row = (
        payload.get("jenis_kelamin", "L"),
        int(payload.get("estimasi_semester", 8)),
        float(payload.get("ipk", 0.0)),
        int(payload.get("total_sks", 0)),
        int(payload.get("jumlah_mk", 0)),
        float(payload.get("persentase_sks", 0.0)),
    )
    return spark.createDataFrame([row], schema)


def _build_feature_pipeline(df):
    gender_indexer = StringIndexer(
        inputCol="jenis_kelamin",
        outputCol="jenis_kelamin_index",
        handleInvalid="keep",
    )
    assembler = VectorAssembler(
        inputCols=["jenis_kelamin_index"] + FEATURE_COLUMNS,
        outputCol="features",
    )
    from pyspark.ml import Pipeline
    pipeline = Pipeline(stages=[gender_indexer, assembler])
    return pipeline.fit(df)


def predict_single(payload: dict) -> dict:
    """
    Memprediksi status kelulusan satu mahasiswa.

    Returns
    -------
    dict
        status, prediction, probability_tepat, probability_terlambat,
        model_available
    """
    nama = payload.get("nama", "").strip() or "Mahasiswa"

    if not _model_exists():
        logger.warning("Model belum dilatih; memakai estimasi fallback.")
        return {
            "nama": nama,
            "prediction": "Tepat Waktu"
            if int(payload.get("estimasi_semester", 8)) <= 8
            else "Terlambat",
            "probability_tepat": None,
            "probability_terlambat": None,
            "model_available": False,
        }

    try:
        spark = get_spark("Prediction Service")
        df = _build_input_frame(spark, payload)
        feature_df = _build_feature_pipeline(df).transform(df)

        from backend.ml.predict import load_model
        model = load_model()
        result = model.transform(feature_df).select(
            "prediction", "probability"
        ).first()

        prediction_idx = int(result["prediction"])
        probabilities = list(result["probability"])

        labels = _resolve_label_order()
        if prediction_idx >= len(labels):
            prediction_label = "Terlambat"
        else:
            prediction_label = labels[prediction_idx]

        prob_tepat = 0.0
        prob_terlambat = 0.0
        for idx, label in enumerate(labels):
            prob = probabilities[idx] if idx < len(probabilities) else 0.0
            if label == "Tepat Waktu":
                prob_tepat = float(prob)
            elif label == "Terlambat":
                prob_terlambat = float(prob)

        return {
            "nama": nama,
            "prediction": prediction_label,
            "probability_tepat": prob_tepat,
            "probability_terlambat": prob_terlambat,
            "model_available": True,
        }
    except Exception as exc:
        logger.exception("Prediksi gagal.")
        raise RuntimeError(f"Prediksi gagal: {exc}") from exc
