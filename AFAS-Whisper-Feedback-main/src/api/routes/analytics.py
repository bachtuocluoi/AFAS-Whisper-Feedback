"""
API routes for analytics and statistics.
"""

from fastapi import APIRouter
from src.api.dependencies import db_dependency
from src.core import models
from typing import Optional, Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/most-fluent-user")
def get_most_fluent_user(db: db_dependency) -> Optional[Dict[str, Any]]:
    """
    Get the user with the best fluency metrics.
    
    Ranking criteria:
    - Lower pause ratio (fewer pauses)
    - Higher speech rate (faster, more fluent speech)
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with user_id, speed_rate, and pause_ratio, or None if no data
    """
    result = (
        db.query(
            models.Submit.user_id,
            models.Fluency.speed_rate,
            models.Fluency.pause_ratio
        )
        .join(models.Fluency, models.Fluency.submit_id == models.Submit.id)
        .order_by(
            models.Fluency.pause_ratio.asc(),   # Fewer pauses
            models.Fluency.speed_rate.desc()    # Faster speech
        )
        .first()
    )
    
    if result:
        return {
            "user_id": result.user_id,
            "speed_rate": result.speed_rate,
            "pause_ratio": result.pause_ratio
        }
    return None


@router.get("/best-lexical-user")
def get_best_lexical_user(db: db_dependency) -> Optional[Dict[str, Any]]:
    """
    Get the user with the best lexical complexity metrics.
    
    Ranking criteria:
    - Higher proportion of advanced vocabulary (B2 + C1 levels)
    - Higher MSTTR (more stable lexical diversity)
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with user_id, msttr, B2, and C1 percentages, or None if no data
    """
    result = (
        db.query(
            models.Submit.user_id,
            models.Lexical.msttr,
            models.Lexical.B2,
            models.Lexical.C1
        )
        .join(models.Lexical, models.Lexical.submit_id == models.Submit.id)
        .order_by(
            (models.Lexical.B2 + models.Lexical.C1).desc(),  # Advanced vocabulary
            models.Lexical.msttr.desc()                       # Stable diversity
        )
        .first()
    )
    
    if result:
        return {
            "user_id": result.user_id,
            "msttr": result.msttr,
            "B2": result.B2,
            "C1": result.C1
        }
    return None


@router.get("/best-pronunciation-user")
def get_best_pronunciation_user(db: db_dependency) -> Optional[Dict[str, Any]]:
    """
    Get the user with the best pronunciation quality.
    
    Ranking criteria:
    - Higher proportion of words with 95-100% confidence
    - Higher proportion of words with 85-95% confidence
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with user_id and confidence scores, or None if no data
    """
    result = (
        db.query(
            models.Submit.user_id,
            models.Pronunciation.score_95_100,
            models.Pronunciation.score_85_95
        )
        .join(models.Pronunciation, models.Pronunciation.submit_id == models.Submit.id)
        .order_by(
            models.Pronunciation.score_95_100.desc(),  # Excellent pronunciation
            models.Pronunciation.score_85_95.desc()    # Good pronunciation
        )
        .first()
    )
    
    if result:
        return {
            "user_id": result.user_id,
            "score_95_100": result.score_95_100,
            "score_85_95": result.score_85_95
        }
    return None

