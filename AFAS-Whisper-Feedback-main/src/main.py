"""
Main FastAPI application entry point.

This module creates and configures the FastAPI application with all routes,
middleware, and database initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.database import engine, Base
from src.core import models
from src.api.routes import api_router
from fastapi.staticfiles import StaticFiles

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="AFAS - Automatic Feedback for Speaking",
    description="""
    AFAS (Automatic Feedback for Speaking) is an intelligent speech assessment system
    that provides automated feedback on speaking performance using Whisper ASR.
    
    ## Features
    
    * **ASR Transcription**: Convert speech to text with word-level timestamps
    * **Fluency Analysis**: Measure speech rate and pause patterns
    * **Lexical Analysis**: Assess vocabulary diversity and CEFR level distribution
    * **Pronunciation Assessment**: Evaluate pronunciation quality using confidence scores
    * **Automated Feedback**: Generate comprehensive feedback based on all metrics
    
    ## API Endpoints
    
    The API provides endpoints for:
    - Transcript management
    - Feature extraction (fluency, lexical, pronunciation)
    - Feedback generation
    - Analytics and statistics
    """,
    version="1.0.0",
    contact={
        "name": "AFAS Development Team",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static HTML files
app.mount("/view", StaticFiles(directory="src/view"), name="view")



@app.get("/")
def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Welcome message and API information
    """
    return {
        "message": "Welcome to AFAS (Automatic Feedback for Speaking) API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "AFAS"}

