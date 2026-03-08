from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session

from db.database import SessionLocal

router = APIRouter()


class TranscriptBase(BaseModel):
    transcript_id: int
    word_index: int
    word: str
    prob: float
    start: float
    end: float


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/transcripts/{submit_id}")
def get_transcripts_by_submit(
    submit_id: int,
    db: db_dependency
):
    transcripts = (
        db.query(db.models.Transcript)
        .filter(db.models.Transcript.submit_id == submit_id)
        .order_by(db.models.Transcript.word_index)
        .all()
    )

    if not transcripts:
        raise HTTPException(status_code=404, detail="Transcript not found")


    return transcripts

@router.post("/transcript/")
def create_transcript(transcript: TranscriptBase, db: db_dependency):
    db_transcript = db.models.Transcript(
        submit_id=transcript.submit_id,
        word_index=transcript.word_index,
        word=transcript.word,
        prob=transcript.prob,
        start=transcript.start,
        end=transcript.end
    )

    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)

    return db_transcript