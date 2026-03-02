"""
Pydantic schemas for Fluency model.
"""

from pydantic import BaseModel


class FluencyBase(BaseModel):
    """Base schema for Fluency with common fields."""
    submit_id: int
    speed_rate: float
    pause_ratio: float


class FluencyCreate(FluencyBase):
    """Schema for creating a new Fluency entry."""
    pass


class FluencyResponse(FluencyBase):
    """Schema for Fluency response."""
    id: int

    class Config:
        from_attributes = True

