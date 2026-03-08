from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session

from db.database import SessionLocal

router = APIRouter()


class FeedbackBase(BaseModel):
    user_id: int
    submit_id: int
    feedback: str
    fluency_id: int
    lexical_id: int
    pronunciation_id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/feedback/{submit_id}")
def get_feedback_by_submit(
    submit_id: int,
    db: db_dependency
):
    feedbacks = (
        db.query(db.models.Feedback)
        .filter(db.models.Feedback.submit_id == submit_id)
        .all()
    )

    return feedbacks



@router.post("/feedback/", status_code=201)
def create_feedback(feedback: FeedbackBase, db: db_dependency):
    db_feedback = db.models.Feedback(
        user_id=feedback.user_id,
        submit_id=feedback.submit_id,
        feedback=feedback.feedback,
        fluency_id=feedback.fluency_id,
        lexical_id=feedback.lexical_id,
        pronunciation_id=feedback.pronunciation_id
    )

    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    return db_feedback