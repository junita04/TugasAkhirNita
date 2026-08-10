"""
Metrik tambahan untuk halaman Training Model.

Menghitung ROC Curve dari DataFrame hasil prediksi (prediction_df) yang
SUDAH dihasilkan oleh modul evaluasi. Service ini hanya membaca hasil
prediksi dan tidak mengubah proses training maupun logika evaluasi.
"""

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _roc_points(labels, scores):
    """Menghitung FPR/TPR untuk setiap threshold dari skor probabilitas.

    Diimplementasikan dengan Python murni (tanpa dependensi sklearn/numpy)
    sehingga aman dipakai di runtime yang minim library.
    """
    pairs = sorted(zip(scores, labels), key=lambda p: -p[0])

    pos_total = sum(1 for _, lbl in pairs if lbl == 1.0)
    neg_total = len(pairs) - pos_total

    if pos_total == 0 or neg_total == 0:
        return None, None, None

    fpr, tpr, thresholds = [], [], []
    tp = 0
    fp = 0
    prev_score = None

    for score, label in pairs:
        if prev_score is not None and score != prev_score:
            fpr.append(fp / neg_total if neg_total else 0.0)
            tpr.append(tp / pos_total if pos_total else 0.0)
            thresholds.append(prev_score)
        if label == 1.0:
            tp += 1
        else:
            fp += 1
        prev_score = score

    fpr.append(fp / neg_total if neg_total else 0.0)
    tpr.append(tp / pos_total if pos_total else 0.0)
    thresholds.append(prev_score)

    return fpr, tpr, thresholds


def _auc(fpr, tpr):
    """Menghitung Area Under Curve dengan metode trapezoid."""
    if not fpr or len(fpr) < 2:
        return 0.0
    area = 0.0
    for i in range(1, len(fpr)):
        area += (fpr[i] - fpr[i - 1]) * (tpr[i] + tpr[i - 1]) / 2.0
    return area


def compute_roc(prediction_df):
    """
    Menghitung titik-titik ROC Curve dan AUC dari DataFrame prediksi biner.

    Parameters
    ----------
    prediction_df : pyspark.sql.DataFrame
        DataFrame hasil prediksi model (memiliki kolom ``probability``
        berisi vektor probabilitas dan kolom ``label``).

    Returns
    -------
    dict | None
        ``{"fpr": [...], "tpr": [...], "thresholds": [...], "auc": float,
        "n_samples": int}`` atau ``None`` bila data tidak dapat dihitung
        (mis. hanya satu kelas).
    """
    if prediction_df is None:
        return None

    try:
        rows = prediction_df.select("probability", "label").collect()
        if not rows:
            return None

        labels = []
        scores = []
        for row in rows:
            prob = row["probability"]
            if prob is None or prob.size < 2 or row["label"] is None:
                continue
            labels.append(float(row["label"]))
            scores.append(float(prob[1]))

        if not labels or len(set(labels)) < 2:
            return None

        fpr, tpr, thresholds = _roc_points(labels, scores)
        if fpr is None:
            return None

        return {
            "fpr": fpr,
            "tpr": tpr,
            "thresholds": thresholds,
            "auc": _auc(fpr, tpr),
            "n_samples": len(labels),
        }
    except Exception as exc:
        logger.warning(f"ROC curve tidak dapat dihitung: {exc}")
        return None
