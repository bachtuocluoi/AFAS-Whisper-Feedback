"""
API routes for pronunciation metrics.
"""

from fastapi import APIRouter, HTTPException
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.pronunciation import PronunciationCreate, PronunciationResponse

router = APIRouter(prefix="/pronunciation", tags=["pronunciation"])


@router.get("/{submit_id}", response_model=PronunciationResponse)
def get_pronunciation(
    submit_id: int,
    db: db_dependency
):
    """
    Get pronunciation metrics for a specific submission.
    
    Args:
        submit_id: ID of the submission
        db: Database session
        
    Returns:
        Pronunciation metrics (confidence score distribution)
        
    Raises:
        HTTPException: 404 if pronunciation metrics not found
    """
    pronunciation = (
        db.query(models.Pronunciation)
        .filter(models.Pronunciation.submit_id == submit_id)
        .first()
    )
    
    if not pronunciation:
        raise HTTPException(status_code=404, detail="Pronunciation metrics not found")
    
    return pronunciation


@router.post("/", response_model=PronunciationResponse, status_code=201)
def create_pronunciation(
    pronunciation: PronunciationCreate,
    db: db_dependency
):
    """
    Create pronunciation metrics for a submission.
    
    Args:
        pronunciation: Pronunciation data to create
        db: Database session
        
    Returns:
        Created pronunciation entry
    """
    db_pronunciation = models.Pronunciation(
        submit_id=pronunciation.submit_id,
        score_0_50=pronunciation.score_0_50,
        score_50_70=pronunciation.score_50_70,
        score_70_85=pronunciation.score_70_85,
        score_85_95=pronunciation.score_85_95,
        score_95_100=pronunciation.score_95_100,
        pronunciation_score = pronunciation.pronunciation_score
    )
    
    db.add(db_pronunciation)
    db.commit()
    db.refresh(db_pronunciation)
    
    return db_pronunciation

