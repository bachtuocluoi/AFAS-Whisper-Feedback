"""
API routes for transcript management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.transcript import TranscriptCreate, TranscriptResponse
from src.auth.get_user import get_current_user, check_submit_owned_user

router = APIRouter(prefix="/transcripts", tags=["transcripts"], dependencies=[Depends(get_current_user)])


@router.get("/{submit_id}", response_model=List[TranscriptResponse], dependencies=[Depends(check_submit_owned_user)])
def get_transcripts_by_submit(
    submit_id: int,
    db: db_dependency
):
    """
    Get all transcript entries for a specific submission.
    
    Args:
        submit_id: ID of the submission
        db: Database session
        
    Returns:
        List of transcript entries ordered by word index
        
    Raises:
        HTTPException: 404 if no transcripts found
    """
    transcripts = (
        db.query(models.Transcript)
        .filter(models.Transcript.submit_id == submit_id)
        .order_by(models.Transcript.word_index)
        .all()
    )
    
    if not transcripts:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return transcripts


@router.post("/", response_model=TranscriptResponse, status_code=201)
def create_transcript(
    transcript: TranscriptCreate,
    db: db_dependency
):
    """
    Create a new transcript entry.
    
    Args:
        transcript: Transcript data to create
        db: Database session
        
    Returns:
        Created transcript entry
    """
    db_transcript = models.Transcript(
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

