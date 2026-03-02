"""
API routes package.
"""

from fastapi import APIRouter
from . import transcripts, fluency, lexical, pronunciation, feedback, analytics

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(transcripts.router)
api_router.include_router(fluency.router)
api_router.include_router(lexical.router)
api_router.include_router(pronunciation.router)
api_router.include_router(feedback.router)
api_router.include_router(analytics.router)

