from fastapi import FastAPI

from backend.api.upload import router as upload_router
from backend.api.train import router as train_router
from backend.api.predict import router as predict_router
from backend.api.pipeline import router as pipeline_router

app = FastAPI(
    title="Academic Graduation Prediction System",
    description="Integrasi Gold Layer Akademik ke Feature Store untuk Prediksi Tingkat Kelulusan Mahasiswa",
    version="1.0.0"
)

app.include_router(upload_router)
app.include_router(train_router)
app.include_router(predict_router)
app.include_router(pipeline_router)


@app.get("/")
def root():
    return {
        "message": "Academic Graduation Prediction API",
        "status": "running"
    }
