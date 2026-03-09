from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.special_queries.fluency_best import get_most_fluent_user

router = APIRouter()


class FluencyBase(BaseModel):
    submit_id: int
    speed_rate: float
    pause_ratio: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/fluency/{submit_id}")
def get_fluency(
    submit_id: int,
    db: db_dependency
):
    fluency = (
        db.query(db.models.Fluency)
        .filter(db.models.Fluency.submit_id == submit_id)
        .first()
    )

    return fluency



@router.post("/fluency/")
def create_fluency(fluency: FluencyBase, db: db_dependency):
    db_fluency = db.models.Fluency(
        submit_id=fluency.submit_id,
        speed_rate=fluency.speed_rate,
        pause_ratio=fluency.pause_ratio
    )

    db.add(db_fluency)
    db.commit()
    db.refresh(db_fluency)

    return db_fluency


@router.get("/fluency/best")
def get_best_fluency(db: db_dependency):
    return get_most_fluent_user(db)