from pydantic import BaseModel

class GrammarBase(BaseModel):
    """Base schema for Grammar with common fields."""

    submit_id: int
    ratio_error_sentences: float
    total_errors: int
    error_rate: float

class GrammarCreate(GrammarBase):
    """Schema for creating a new Grammar entry."""
    pass


class GrammarResponse(GrammarBase):
    """Schema for Grammar response."""
    id: int
    
    class Config:
        from_attributes = True

