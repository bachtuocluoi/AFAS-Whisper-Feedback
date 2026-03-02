"""
Pydantic schemas for Transcript model.
"""

from pydantic import BaseModel


class TranscriptBase(BaseModel):
    """Base schema for Transcript with common fields."""
    submit_id: int
    word_index: int
    word: str
    prob: float
    start: float
    end: float


class TranscriptCreate(TranscriptBase):
    """Schema for creating a new Transcript entry."""
    pass


class TranscriptResponse(TranscriptBase):
    """Schema for Transcript response."""
    id: int

    class Config:
        from_attributes = True

