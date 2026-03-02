"""
Pydantic schemas for Feedback model.
"""

from pydantic import BaseModel
from typing import Optional


class FeedbackBase(BaseModel):
    """Base schema for Feedback with common fields."""
    user_id: int
    submit_id: int
    feedback: str
    fluency_id: Optional[int] = None
    lexical_id: Optional[int] = None
    pronunciation_id: Optional[int] = None


class FeedbackCreate(FeedbackBase):
    """Schema for creating a new Feedback entry."""
    pass


class FeedbackResponse(FeedbackBase):
    """Schema for Feedback response."""
    id: int

    class Config:
        from_attributes = True

