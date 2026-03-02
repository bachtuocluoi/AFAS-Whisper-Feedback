"""
FastAPI dependencies for database and service access.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from src.core.database import get_db

# Type alias for database dependency
db_dependency = Annotated[Session, Depends(get_db)]

