from backend.ml.predict import predict

prediction_df = predict()

prediction_df.select(
    "jenis_kelamin",
    "ipk",
    "total_sks",
    "prediction",
    "probability"
).show(20, truncate=False)