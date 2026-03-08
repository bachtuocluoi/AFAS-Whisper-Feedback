from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Annotated
import db.models
from db.database import SessionLocal, engine
from sqlalchemy.orm import Session





app = FastAPI(
    title="Automatic Speech Recognition ASR",
    description="ASR pipeline with Whisper",
    version="1.0.0"
)

db.models.Base.metadata.create_all(bind=engine)


class SubmitBase(BaseModel):
    user_id: int
    audio_path: str
    asr_type: str = "whisper"






@app.get("/")
def check():
    return {"message": f"Hello student"}



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]







def get_most_fluent_user(db: Session):
    return (
        db.query(
            db.models.Submit.user_id,
            db.models.Fluency.speed_rate,
            db.models.Fluency.pause_ratio
        )
        .join(db.models.Fluency, db.models.Fluency.submit_id == db.models.Submit.id)
        .order_by(
            db.models.Fluency.pause_ratio.asc(),   # ít pause nhất
            db.models.Fluency.speed_rate.desc()    # nói đều + nhanh
        )
        .first()
    )



def get_best_lexical_user(db: Session):
    return (
        db.query(
            db.models.Submit.user_id,
            db.models.Lexical.mttr,
            db.models.Lexical.B2,
            db.models.Lexical.C1
        )
        .join(db.models.Lexical, db.models.Lexical.submit_id == db.models.Submit.id)
        .order_by(
            (db.models.Lexical.B2 + db.models.Lexical.C1).desc(),  # độ khó từ vựng
            db.models.Lexical.mttr.desc()                           # ổn định lexical
        )
        .first()
    )



def get_best_pronunciation_user(db: Session):
    return (
        db.query(
            db.models.Submit.user_id,
            db.models.Pronunciation.score_95_100,
            db.models.Pronunciation.score_85_95
        )
        .join(db.models.Pronunciation, db.models.Pronunciation.submit_id == db.models.Submit.id)
        .order_by(
            db.models.Pronunciation.score_95_100.desc(),
            db.models.Pronunciation.score_85_95.desc()
        )
        .first()
    )




