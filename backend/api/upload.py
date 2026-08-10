from pathlib import Path
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.pipeline_service import run_pipeline

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file Excel kemudian menjalankan seluruh pipeline ETL.
    """

    try:

        # Validasi file
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=400,
                detail="File harus berupa Excel (.xlsx atau .xls)"
            )

        # Simpan file
        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Jalankan Pipeline
        run_pipeline(file_path)

        return {
            "status": "success",
            "message": "Pipeline berhasil dijalankan.",
            "file": file.filename
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/file")
async def upload_file_only(file: UploadFile = File(...)):
    """
    Menyimpan file Excel ke folder data/ tanpa menjalankan pipeline.
    Digunakan oleh halaman Upload sebelum tombol "Jalankan Pipeline".
    """

    try:

        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=400,
                detail="File harus berupa Excel (.xlsx atau .xls)"
            )

        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "status": "success",
            "message": "File berhasil diunggah.",
            "file": file.filename
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# uvicorn main:app --reload