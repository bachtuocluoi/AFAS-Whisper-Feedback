"""
Pydantic schemas for Submit model.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubmitBase(BaseModel):
    """Base schema for Submit with common fields."""
    user_id: int
    audio_path: str
    asr_type: str = "whisper"


class SubmitCreate(SubmitBase):
    """Schema for creating a new Submit."""
    pass


class SubmitResponse(SubmitBase):
    """Schema for Submit response."""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

