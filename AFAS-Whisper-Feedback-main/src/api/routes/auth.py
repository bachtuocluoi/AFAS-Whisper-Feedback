"""
API route for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.models import User
from src.schemas.login import LoginRequest, TokenResponse, RegisterRequest
from src.auth.auth import verify_password, create_access_token, hash_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == payload.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "username": new_user.username
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Invalid username or password")

    access_token = create_access_token(user_id=user.id, username=user.username)

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer"
    )