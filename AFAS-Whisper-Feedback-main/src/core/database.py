"""
Database configuration and session management.

This module provides database engine, session factory, and base model class
for SQLAlchemy ORM operations.
"""

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Naming convention
metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })
# Base class for all models
Base = declarative_base(metadata=metadata)


def get_db():
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        Used as FastAPI dependency:
        ```python
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

