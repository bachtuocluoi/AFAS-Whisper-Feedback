"""
Database models for AFAS system.

This module defines all SQLAlchemy ORM models representing the database schema
for submissions, transcripts, and feature extraction results.
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base


class Submit(Base):
    """
    Model representing a user submission of an audio file for analysis.
    
    Attributes:
        id: Primary key
        user_id: ID of the user who submitted the audio
        asr_type: Type of ASR system used (default: "whisper")
        audio_path: File path to the submitted audio
        created_at: Timestamp of submission
    """
    __tablename__ = "submit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    asr_type = Column(String(50), index=True, default="whisper")
    audio_path = Column(String, nullable=False)
    created_at = Column(DateTime)

    # Relationships
    transcript = relationship("Transcript", back_populates="submit", uselist=False)
    fluency = relationship("Fluency", back_populates="submit", uselist=False)
    lexical = relationship("Lexical", back_populates="submit", uselist=False)
    pronunciation = relationship("Pronunciation", back_populates="submit", uselist=False)
    feedbacks = relationship("Feedback", back_populates="submit")


class Transcript(Base):
    """
    Model storing word-level transcription results from ASR.
    
    Each row represents a single word with its timestamp and confidence score.
    
    Attributes:
        id: Primary key
        submit_id: Foreign key to Submit table
        word_index: Position of word in the transcript (0-indexed)
        word: The transcribed word text
        prob: Confidence probability from ASR model (0.0 to 1.0)
        start: Start time of word in seconds
        end: End time of word in seconds
    """
    __tablename__ = "transcript"

    id = Column(Integer, primary_key=True)
    submit_id = Column(Integer, ForeignKey("submit.id"), index=True)
    word_index = Column(Integer, nullable=False)
    word = Column(String, nullable=False)
    prob = Column(Float, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)

    # Relationship
    submit = relationship("Submit", back_populates="transcript")


class Fluency(Base):
    """
    Model storing fluency metrics extracted from speech.
    
    Fluency measures the smoothness and naturalness of speech delivery.
    
    Attributes:
        id: Primary key
        submit_id: Foreign key to Submit table (one-to-one)
        speed_rate: Speech rate in words per second
        pause_ratio: Ratio of pause time to total duration (0.0 to 1.0)
    """
    __tablename__ = "fluency"

    id = Column(Integer, primary_key=True)
    submit_id = Column(Integer, ForeignKey("submit.id"), unique=True, index=True)
    speed_rate = Column(Float, nullable=False)  # words per second
    pause_ratio = Column(Float, nullable=False)  # pause time / total duration

    # Relationship
    submit = relationship("Submit", back_populates="fluency")


class Lexical(Base):
    """
    Model storing lexical complexity metrics.
    
    Measures vocabulary diversity and CEFR level distribution.
    
    Attributes:
        id: Primary key
        submit_id: Foreign key to Submit table (one-to-one)
        ttr: Type-Token Ratio (vocabulary diversity measure)
        msttr: Mean Segmental Type-Token Ratio (more stable diversity measure)
        A1, A2, B1, B2, C1: Percentage of words at each CEFR level
    """
    __tablename__ = "lexical"

    id = Column(Integer, primary_key=True)
    submit_id = Column(Integer, ForeignKey("submit.id"), unique=True, index=True)
    
    # Lexical diversity metrics
    ttr = Column(Float, nullable=False)  # Type-Token Ratio
    msttr = Column(Float, nullable=False)  # Mean Segmental TTR
    
    # CEFR level distribution (percentages)
    A1 = Column(Float, nullable=False)
    A2 = Column(Float, nullable=False)
    B1 = Column(Float, nullable=False)
    B2 = Column(Float, nullable=False)
    C1 = Column(Float, nullable=False)

    # Relationship
    submit = relationship("Submit", back_populates="lexical")


class Pronunciation(Base):
    """
    Model storing pronunciation quality metrics.
    
    Measures pronunciation accuracy based on ASR confidence scores.
    
    Attributes:
        id: Primary key
        submit_id: Foreign key to Submit table (one-to-one)
        score_0_50: Percentage of words with confidence 0-50%
        score_50_70: Percentage of words with confidence 50-70%
        score_70_85: Percentage of words with confidence 70-85%
        score_85_95: Percentage of words with confidence 85-95%
        score_95_100: Percentage of words with confidence 95-100%
        pronunciation_score: float # average of all percentages
    """
    __tablename__ = "pronunciation"

    id = Column(Integer, primary_key=True)
    submit_id = Column(Integer, ForeignKey("submit.id"), unique=True, index=True)
    
    # Confidence score distribution (percentages)
    score_0_50 = Column(Float, nullable=False)
    score_50_70 = Column(Float, nullable=False)
    score_70_85 = Column(Float, nullable=False)
    score_85_95 = Column(Float, nullable=False)
    score_95_100 = Column(Float, nullable=False)
    pronunciation_score = Column(Float, nullable=False)

    # Relationship
    submit = relationship("Submit", back_populates="pronunciation")


class Feedback(Base):
    """
    Model storing generated feedback text for submissions.
    
    Attributes:
        id: Primary key
        submit_id: Foreign key to Submit table
        user_id: ID of the user receiving feedback
        feedback: Text content of the feedback
        fluency_id: Reference to fluency metrics used
        lexical_id: Reference to lexical metrics used
        pronunciation_id: Reference to pronunciation metrics used
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    submit_id = Column(Integer, ForeignKey("submit.id"), index=True)
    user_id = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=False)
    fluency_id = Column(Integer, nullable=True)
    lexical_id = Column(Integer, nullable=True)
    pronunciation_id = Column(Integer, nullable=True)

    # Relationship
    submit = relationship("Submit", back_populates="feedbacks")

