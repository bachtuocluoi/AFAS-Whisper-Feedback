"""
Configuration settings for AFAS (Automatic Feedback for Speaking) system.

This module contains all configuration parameters for the application,
including database settings, model paths, and feature extraction parameters.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or defaults.
    
    Attributes:
        database_url: SQLite database connection string
        whisper_model: Whisper model name to use (e.g., "base.en")
        pause_threshold: Minimum gap duration (seconds) to consider as a pause
        msttr_segment_size: Segment size for Mean Segmental Type-Token Ratio calculation
        cefr_dict_path: Path to CEFR level dictionary CSV file
    """
    
    # Database Configuration
    database_url: str = "sqlite:///./asr.db"
    
    # Whisper ASR Configuration
    whisper_model: str = "base.en"
    
    # Feature Extraction Parameters
    pause_threshold: float = 0.25  # seconds
    msttr_segment_size: int = 50
    
    # Data Paths
    cefr_dict_path: str = "data/oxford_cerf.csv"

    backend_base_url: str = "http://127.0.0.1:8100"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

