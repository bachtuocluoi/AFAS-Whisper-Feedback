"""
API routes for lexical metrics.
"""

from fastapi import APIRouter, HTTPException
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.lexical import LexicalCreate, LexicalResponse

router = APIRouter(prefix="/lexical", tags=["lexical"])


@router.get("/{submit_id}", response_model=LexicalResponse)
def get_lexical(
    submit_id: int,
    db: db_dependency
):
    """
    Get lexical metrics for a specific submission.
    
    Args:
        submit_id: ID of the submission
        db: Database session
        
    Returns:
        Lexical metrics (TTR, MSTTR, CEFR level distribution)
        
    Raises:
        HTTPException: 404 if lexical metrics not found
    """
    lexical = (
        db.query(models.Lexical)
        .filter(models.Lexical.submit_id == submit_id)
        .first()
    )
    
    if not lexical:
        raise HTTPException(status_code=404, detail="Lexical metrics not found")
    
    return lexical


@router.post("/", response_model=LexicalResponse, status_code=201)
def create_lexical(
    lexical: LexicalCreate,
    db: db_dependency
):
    """
    Create lexical metrics for a submission.
    
    Args:
        lexical: Lexical data to create
        db: Database session
        
    Returns:
        Created lexical entry
    """
    db_lexical = models.Lexical(
        submit_id=lexical.submit_id,
        ttr=lexical.ttr,
        msttr=lexical.msttr,
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

