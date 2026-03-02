"""
API routes for fluency metrics.
"""

from fastapi import APIRouter, HTTPException
from src.api.dependencies import db_dependency
from src.core import models
from src.schemas.fluency import FluencyCreate, FluencyResponse

router = APIRouter(prefix="/fluency", tags=["fluency"])


@router.get("/{submit_id}", response_model=FluencyResponse)
def get_fluency(
    submit_id: int,
    db: db_dependency
):
    """
    Get fluency metrics for a specific submission.
    
    Args:
        submit_id: ID of the submission
        db: Database session
        
    Returns:
        Fluency metrics (speed_rate, pause_ratio)
        
    Raises:
        HTTPException: 404 if fluency metrics not found
    """
    fluency = (
        db.query(models.Fluency)
        .filter(models.Fluency.submit_id == submit_id)
        .first()
    )
    
    if not fluency:
        raise HTTPException(status_code=404, detail="Fluency metrics not found")
    
    return fluency


@router.post("/", response_model=FluencyResponse, status_code=201)
def create_fluency(
    fluency: FluencyCreate,
    db: db_dependency
):
    """
    Create fluency metrics for a submission.
    
    Args:
        fluency: Fluency data to create
        db: Database session
        
    Returns:
        Created fluency entry
    """
    db_fluency = models.Fluency(
        submit_id=fluency.submit_id,
        speed_rate=fluency.speed_rate,
        pause_ratio=fluency.pause_ratio
    )
    
    db.add(db_fluency)
    db.commit()
    db.refresh(db_fluency)
    
    return db_fluency

