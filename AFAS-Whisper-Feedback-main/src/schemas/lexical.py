"""
Pydantic schemas for Lexical model.
"""

from pydantic import BaseModel


class LexicalBase(BaseModel):
    """Base schema for Lexical with common fields."""
    submit_id: int
    ttr: float
    msttr: float
    A1: float  # Percentage of A1 level words
    A2: float  # Percentage of A2 level words
    B1: float  # Percentage of B1 level words
    B2: float  # Percentage of B2 level words
    C1: float  # Percentage of C1 level words


class LexicalCreate(LexicalBase):
    """Schema for creating a new Lexical entry."""
    pass


class LexicalResponse(LexicalBase):
    """Schema for Lexical response."""
    id: int

    class Config:
        from_attributes = True

