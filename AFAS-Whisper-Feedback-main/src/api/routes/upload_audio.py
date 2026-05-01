"""
API route for uploading audio files.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from src.auth.get_user import get_current_user

router = APIRouter(tags=["upload"], dependencies=[Depends(get_current_user)])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload audio file and return server audio_path.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    file_ext = Path(file.filename).suffix.lower()

    allowed_exts = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".mp4"}

    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {file_ext}"
        )

    unique_filename = f"{uuid4()}{file_ext}"
    save_path = UPLOAD_DIR / unique_filename

    try:
        content = await file.read()

        with open(save_path, "wb") as f:
            f.write(content)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    return {
        "message": "File uploaded successfully",
        "audio_path": str(save_path.resolve()),
        "filename": unique_filename
    }