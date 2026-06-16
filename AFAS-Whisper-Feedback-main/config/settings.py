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
        whisper_model: Whisper model name to use (e.g., "small.en")
        pause_threshold: Minimum gap duration (seconds) to consider as a pause
        msttr_segment_size: Segment size for Mean Segmental Type-Token Ratio calculation
        cefr_dict_path: Path to CEFR level dictionary CSV file
    """
    
    # Database Configuration
    database_url: str 
    
    # Whisper ASR Configuration
    whisper_model: str
    
    # Feature Extraction Parameters
    pause_threshold: float #seconds
    msttr_segment_size: int 
    
    # Data Paths
    cefr_dict_path: str

    backend_base_url: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    SECRET_KEY: str
    JWT_ALG: str
    ACCESS_TOKEN_EXPIRE_SECONDS: int 


# Global settings instance
settings = Settings()

