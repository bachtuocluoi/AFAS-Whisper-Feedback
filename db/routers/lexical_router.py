from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.special_queries.pronunciation_best import get_best_pronunciation_user

router = APIRouter()


class LexicalBase(BaseModel):
    lexical_id: int
    ttr: float
    mttr: float
    A1: float #%A1 trong câu
    A2: float
    B1: float
    B2: float
    C1: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]



@router.get("/lexical/{submit_id}")
def get_lexical(
    submit_id: int,
    db: db_dependency
):
    lexical = (
        db.query(db.models.Lexical)
        .filter(db.models.Lexical.submit_id == submit_id)
        .first()
    )

    return lexical


@router.post("/lexical/", status_code=201)
def create_lexical(lexical: LexicalBase, db: db_dependency):
    db_lexical = db.models.Lexical(
        submit_id=lexical.submit_id,
        ttr=lexical.ttr,
        mttr=lexical.mttr,
        A1=lexical.A1,
        A2=lexical.A2,
        B1=lexical.B1,
        B2=lexical.B2,
        C1=lexical.C1
    )

    db.add(db_lexical)
    db.commit()
    db.refresh(db_lexical)

    return db_lexical



@router.get("/lexical/best")
def get_best_fluency(db: db_dependency):
    return get_best_pronunciation_user(db)