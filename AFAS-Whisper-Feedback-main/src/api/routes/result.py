from fastapi import APIRouter, HTTPException
from src.api.dependencies import db_dependency
from src.core import models
from src.services.result_chart_service import (
    build_lexical_bar_chart,
    build_lexical_diversity_chart,
    build_pronunciation_bar_chart,
)

router = APIRouter(prefix="/result", tags=["result"])


def parse_feedback_text(text: str):
    result = {
        "fluency": "",
        "pause": "",
        "lexical_diversity": "",
        "lexical_level": "",
        "pronunciation": ""
    }

    if not text:
        return result

    labels = [
        ("fluency", "Fluency:"),
        ("pause", "Pause:"),
        ("lexical_diversity", "Lexical diversity:"),
        ("lexical_level", "Lexical level:"),
        ("pronunciation", "Pronunciation:")
    ]

    for i, (key, label) in enumerate(labels):
        start = text.find(label)
        if start == -1:
            continue

        content_start = start + len(label)
        content_end = len(text)

        for j in range(i + 1, len(labels)):
            next_label = labels[j][1]
            next_start = text.find(next_label)
            if next_start != -1 and next_start > start:
                content_end = next_start
                break

        result[key] = text[content_start:content_end].strip().rstrip(".")

    return result


@router.get("/{submit_id}")
def get_result_dashboard(submit_id: int, db: db_dependency):
    fluency = db.query(models.Fluency).filter(models.Fluency.submit_id == submit_id).first()
    lexical = db.query(models.Lexical).filter(models.Lexical.submit_id == submit_id).first()
    pronunciation = db.query(models.Pronunciation).filter(models.Pronunciation.submit_id == submit_id).first()
    feedback = db.query(models.Feedback).filter(models.Feedback.submit_id == submit_id).first()

    if not fluency and not lexical and not pronunciation and not feedback:
        raise HTTPException(status_code=404, detail="No result data found")

    payload = {
        "fluency": None,
        "lexical": None,
        "pronunciation": None,
        "feedback": None,
        "charts": {}
    }

    if fluency:
        payload["fluency"] = {
            "speed_rate": round(float(fluency.speed_rate), 2),
            "pause_ratio": round(float(fluency.pause_ratio), 2)
        }

    if lexical:
        payload["lexical"] = {
            "ttr": round(float(lexical.ttr), 2),
            "mttr": round(float(lexical.mttr), 2),
            "A1": round(float(lexical.A1), 2),
            "A2": round(float(lexical.A2), 2),
            "B1": round(float(lexical.B1), 2),
            "B2": round(float(lexical.B2), 2),
            "C1": round(float(lexical.C1), 2)
        }
        payload["charts"]["lexical_bar"] = build_lexical_bar_chart(payload["lexical"]).to_dict()
        payload["charts"]["lexical_diversity_bar"] = build_lexical_diversity_chart(payload["lexical"]).to_dict()

    if pronunciation:
        payload["pronunciation"] = {
            "score_0_50": round(float(pronunciation.score_0_50), 2),
            "score_50_70": round(float(pronunciation.score_50_70), 2),
            "score_70_85": round(float(pronunciation.score_70_85), 2),
            "score_85_95": round(float(pronunciation.score_85_95), 2),
            "score_95_100": round(float(pronunciation.score_95_100), 2),
            "pronunciation_score": round(float(pronunciation.pronunciation_score), 2)

        }
        payload["charts"]["pronunciation_bar"] = build_pronunciation_bar_chart(payload["pronunciation"]).to_dict()

    if feedback:
        payload["feedback"] = parse_feedback_text(feedback.feedback)

    return payload