from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Annotated
import db.models
from db.database import SessionLocal, engine
from sqlalchemy.orm import Session
from routers import transcript, fluency, lexical, pronunciation, feedback





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


db.models.Base.metadata.create_all(bind=engine)

app.include_router(transcript.router)
app.include_router(fluency.router)
app.include_router(lexical.router)
app.include_router(pronunciation.router)
app.include_router(feedback.router)




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


















