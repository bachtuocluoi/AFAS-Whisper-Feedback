"""
API routes for submit management - handles submit creation and ASR transcription.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.services.fluency_service import compute_fluency_metrics
from src.services.pronunciation_service import compute_pronunciation_metrics
from src.services.lexical_cefr_service import compute_lexical_cefr_metrics
from src.services.lexical_diversity_service import compute_lexical_diversity_metrics
from src.services.feedback_service import generate_feedback

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

            # 5. Tính và lưu fluency
    try:
        fluency_data = compute_fluency_metrics(result)

        db_fluency = models.Fluency(
            submit_id=db_submit.id,
            speed_rate=fluency_data["speech_rate"],
            pause_ratio=fluency_data["pause_ratio"]
        )
        db.add(db_fluency)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save fluency: {str(e)}"
        )

    # 6. Tính và lưu lexical
    try:
        lexical_cefr = compute_lexical_cefr_metrics(result)
        lexical_diversity = compute_lexical_diversity_metrics(result)

        db_lexical = models.Lexical(
            submit_id=db_submit.id,
            ttr=lexical_diversity["ttr"],
            mttr=lexical_diversity["mttr"],
            A1=lexical_cefr["a1"],
            A2=lexical_cefr["a2"],
            B1=lexical_cefr["b1"],
            B2=lexical_cefr["b2"],
            C1=lexical_cefr["c1"]
        )
        db.add(db_lexical)
        db.commit()
        db.refresh(db_lexical)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save lexical: {str(e)}"
        )

    # 7. Tính và lưu pronunciation
    try:
        pronunciation_data = compute_pronunciation_metrics(result)

        db_pronunciation = models.Pronunciation(
            submit_id=db_submit.id,
            score_0_50 = pronunciation_data["score_0_50"],
            score_50_70 = pronunciation_data["score_50_70"],
            score_70_85 = pronunciation_data["score_70_85"],
            score_85_95=pronunciation_data["score_85_95"],
            score_95_100=pronunciation_data["score_95_100"]
        )
        db.add(db_pronunciation)
        db.commit()
        db.refresh(db_pronunciation)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save pronunciation: {str(e)}"
        )

    # 8. Tạo và lưu feedback
    try:
        features = {
            "speech_rate": fluency_data["speech_rate"],
            "pause_ratio": fluency_data["pause_ratio"],
            "ttr": lexical_diversity["ttr"],
            "msttr": lexical_diversity["mttr"],
            "a1": lexical_cefr["a1"],
            "a2": lexical_cefr["a2"],
            "b1": lexical_cefr["b1"],
            "b2": lexical_cefr["b2"],
            "c1": lexical_cefr["c1"],
            "score_0_50": pronunciation_data["score_0_50"],
            "score_50_70": pronunciation_data["score_50_70"],
            "score_70_85": pronunciation_data["score_70_85"],
            "score_85_95": pronunciation_data["score_85_95"],
            "score_95_100": pronunciation_data["score_95_100"],
            "pronunciation": pronunciation_data["pronunciation_score"]
        }


        feedback_result = generate_feedback(features)

        feedback_text = (
            f"Fluency: {feedback_result['fluency']}<br>"
            f"Pause: {feedback_result['pause']}<br>"
            f"Lexical diversity: {feedback_result['lexical_diversity']}<br>"
            f"Lexical level: {feedback_result['lexical_level']}<br>"
            f"Pronunciation: {feedback_result['pronunciation']}"
        )

        db_feedback = models.Feedback(
            submit_id=db_submit.id,
            user_id=db_submit.user_id,
            feedback=feedback_text
        )

        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}"
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

