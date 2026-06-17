from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src import models
from src.database import get_db
from src.auth import get_current_user
from src.schemas.grammar import GrammarCreate, GrammarResponse
from src.services.grammar_service import compute_grammar_metrics


"""
API routes for grammar metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.fluency import GrammarCreate, GrammarResponse
from src.auth.get_user import get_current_user, check_submit_owned_user


router = APIRouter(prefix="/grammar",tags=["grammar"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=GrammarResponse, status_code=201)
def create_grammar_metrics(
    grammar: GrammarCreate,
    db: db_dependency
):
    """
    Compute and save grammar metrics for a speaking submission.

    Grammar is computed from the transcript words that were already generated
    by Whisper ASR and stored in the Transcript table.
    """


    # 6. Lưu grammar vào database
    db_grammar = models.Grammar(
        submit_id=grammar.submit_id,
        ratio_error_sentences=grammar.ratio_error_sentences,
        total_errors=grammar.total_errors,
        error_rate=grammar.error_rate
    )

    db.add(db_grammar)
    db.commit()
    db.refresh(db_grammar)

    return db_grammar




@router.get("/{submit_id}", response_model=GrammarResponse, dependencies=[Depends(check_submit_owned_user)])
def get_grammar_metrics(
    submit_id: int,
    db: db_dependency
):
    """
    Get grammar metrics for a specific submission.
    
    Args:
        submit_id: ID of the submission
        db: Database session
        
    Returns:
        Grammar metrics (ratio_error_sentences, total_errors, error_rate)
        
    Raises:
        HTTPException: 404 if fluency metrics not found
    """

    grammar = (
        db.query(models.Grammar)
        .filter(models.Grammar.submit_id == submit_id)
        .first()
    )

    if not grammar:
        raise HTTPException(
            status_code=404,
            detail="Grammar metrics not found"
        )

    return grammar