from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.special_queries.pronunciation_best import get_best_pronunciation_user

router = APIRouter()


class PronunciationBase(BaseModel):
    pronunciation_id: int
    score_0_50: float
    score_50_70: float
    score_70_85: float
    score_85_95: float
    score_95_100: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]



@router.get("/pronunciation/{submit_id}")
def get_pronunciation(
    submit_id: int,
    db: db_dependency
):
    pronunciation = (
        db.query(db.models.Pronunciation)
        .filter(db.models.Pronunciation.submit_id == submit_id)
        .first()
    )

    return pronunciation


@router.post("/pronunciation/")
def create_pronunciation(pronunciation: PronunciationBase, db: db_dependency):
    db_pronunciation = db.models.Pronunciation(
        submit_id=pronunciation.submit_id,
        score_0_50=pronunciation.score_0_50,
        score_50_70=pronunciation.score_50_70,
        score_70_85=pronunciation.score_70_85,
        score_85_95=pronunciation.score_85_95,
        score_95_100=pronunciation.score_95_100
    )

    db.add(db_pronunciation)
    db.commit()
    db.refresh(db_pronunciation)

    return db_pronunciation


@router.get("/pronunciation/best")
def get_best_fluency(db: db_dependency):
    return get_best_pronunciation_user(db)