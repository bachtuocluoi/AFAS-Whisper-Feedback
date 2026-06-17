from pydantic import BaseModel
from typing import Optional


class ScoreBase(BaseModel):

    """
    Base schema for Score with common fields.

    Attributes:
        submit_id: Related submission ID
        user_id: Related user ID
        fluency_score: Fluency evaluation score
        lexical_score: Vocabulary / lexical score
        pronunciation_score: Pronunciation evaluation score
        overall_score: Final combined speaking score
        shap_values: Local SHAP explanation stored as JSON string
        
    """
    
    id: int
    submit_id: int
    user_id: int
    fluency_score: Optional[float] = None
    lexical_score: Optional[float] = None
    pronunciation_score: Optional[float] = None
    grammar_score: Optional[float] = None
    overall_score: Optional[float] = None
    shap_values: Optional[str] = None


class ScoreCreate(ScoreBase):
    """
    Schema for creating a new Score entry.
    """
    pass

class ScoreResponse(ScoreBase):
    """
    Schema for Score response.
    """

    id: int

    class Config:
        """
        Enable compatibility with SQLAlchemy ORM models.
        """
        from_attributes = True