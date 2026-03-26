"""
API routes for feedback management.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/{submit_id}", response_model=FeedbackResponse)
def get_feedback_by_submit(
    submit_id: int,
    db: db_dependency
):
    """
    Get all feedback entries for a specific submission.
    
    Args:
        submit_id: ID of the submission
        db: Database session
        
    Returns:
        List of feedback entries
    """
    feedback = (
        db.query(models.Feedback)
        .filter(models.Feedback.submit_id == submit_id)
        .first()
    )

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return feedback



@router.post("/", response_model=FeedbackResponse, status_code=201)
def create_feedback(
    feedback: FeedbackCreate,
    db: db_dependency
):
    """
    Create a new feedback entry.
    
    Args:
        feedback: Feedback data to create
        db: Database session
        
    Returns:
        Created feedback entry
    """
    db_feedback = models.Feedback(
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

