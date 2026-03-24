"""
Pydantic schemas for Pronunciation model.
"""

from pydantic import BaseModel


class PronunciationBase(BaseModel):
    """Base schema for Pronunciation with common fields."""
    submit_id: int
    score_0_50: float    # Percentage of words with 0-50% confidence
    score_50_70: float   # Percentage of words with 50-70% confidence
    score_70_85: float   # Percentage of words with 70-85% confidence
    score_85_95: float   # Percentage of words with 85-95% confidence
    score_95_100: float  # Percentage of words with 95-100% confidence
    pronunciation_score: float # average of all percentages


class PronunciationCreate(PronunciationBase):
    """Schema for creating a new Pronunciation entry."""
    pass


class PronunciationResponse(PronunciationBase):
    """Schema for Pronunciation response."""
    id: int

    class Config:
        from_attributes = True

