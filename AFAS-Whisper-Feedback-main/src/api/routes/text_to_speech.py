from pathlib import Path

from fastapi import APIRouter
from gtts import gTTS

router = APIRouter(tags=["text_to_speech"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/text_to_speech")
async def text_to_speech(text: str, filename: str = "audio.mp3", accent: str = "ae"):
    dom = "us"
    if accent == "be":
        dom = "co.uk"
    save_path = UPLOAD_DIR / filename
    gTTS(text=text, lang='en', tld=dom, slow=False).save(save_path)
    return {
        "message": "File uploaded successfully",
        "audio_path": str(save_path.resolve()),
        "filename": filename
    }