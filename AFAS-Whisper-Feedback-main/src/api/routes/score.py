from fastapi import APIRouter, HTTPException, Depends
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.score import ScoreResponse, ScoreCreate
from src.auth.get_user import get_current_user, check_submit_owned_user

router = APIRouter(prefix="/score", tags=["score"], dependencies=[Depends(get_current_user)])


@router.get("/{submit_id}", response_model=ScoreResponse, dependencies=[Depends(check_submit_owned_user)])
def get_score(submit_id: int, db: db_dependency):
    score = (
        db.query(models.Score)
        .filter(models.Score.submit_id == submit_id)
        .first()
    )

    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    return score


@router.post("/", response_model=ScoreResponse, status_code=201)
def create_score(
    score: ScoreCreate,
    db: db_dependency
):
    """
    Create a new score entry.
    """
    db_score = models.Score(
        submit_id=score.submit_id,
        user_id=score.user_id,
        fluency_score=score.fluency_score,
        lexical_score=score.lexical_score,
        pronunciation_score=score.pronunciation_score,
        grammar_score=score.grammar_score,
        overall_score=score.overall_score,
        shap_values=score.shap_values
    )

    db.add(db_score)
    db.commit()
    db.refresh(db_score)

    return db_score