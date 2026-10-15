from backend.feature_store.inference_dataset import create_inference_dataset

df = create_inference_dataset()

df.select(
    "jenis_kelamin",
    "jenis_kelamin_index",
    "features"
).show(10, truncate=False)