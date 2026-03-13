"""
API routes for submit management - handles submit creation and ASR transcription.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.submit import SubmitCreate, SubmitResponse
from src.services.asr_service import get_asr_service

router = APIRouter(prefix="/submit", tags=["submit"])


@router.post("/", response_model=SubmitResponse, status_code=201)
def submit_audio(
    submit: SubmitCreate,
    db: db_dependency
):
    """
    Create submit record from uploaded audio_path, run ASR, save transcripts.
    """

    # 1. Kiểm tra file path có tồn tại không
    import os
    if not os.path.exists(submit.audio_path):
        raise HTTPException(
            status_code=400,
            detail=f"Audio file not found: {submit.audio_path}"
        )

    # 2. Tạo Submit record
    try:
        db_submit = models.Submit(
            user_id=submit.user_id,
            audio_path=submit.audio_path,
            asr_type=submit.asr_type,
            created_at=datetime.now()
        )

        db.add(db_submit)
        db.commit()
        db.refresh(db_submit)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create submit record: {str(e)}"
        )

    # 3. Chạy ASR Whisper
    try:
        asr_service = get_asr_service()
        result = asr_service.transcribe(
            submit.audio_path,
            word_timestamps=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ASR transcription failed: {str(e)}"
        )

    # 4. Lưu transcript vào database
    try:
        word_index = 0

        if "segments" in result:
            for seg in result["segments"]:
                if "words" in seg:
                    for w in seg["words"]:
                        word = w.get("word", "").strip()
                        if not word:
                            continue

                        prob = w.get("probability", 0.0)
                        start = w.get("start", 0.0)
                        end = w.get("end", 0.0)

                        db_transcript = models.Transcript(
                            submit_id=db_submit.id,
                            word_index=word_index,
                            word=word,
                            prob=prob,
                            start=start,
                            end=end
                        )

                        db.add(db_transcript)
                        word_index += 1

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save transcripts: {str(e)}"
        )

    return db_submit


@router.get("/{submit_id}", response_model=SubmitResponse)
def get_submit(
    submit_id: int,
    db: db_dependency
):
    submit = db.query(models.Submit).filter(models.Submit.id == submit_id).first()

    if not submit:
        raise HTTPException(status_code=404, detail="Submit not found")

    return submit

