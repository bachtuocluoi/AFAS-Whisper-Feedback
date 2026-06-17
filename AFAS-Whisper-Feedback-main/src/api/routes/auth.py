"""
API route for authentication.
"""

from ast import Store
from hmac import new
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.models import User, RefreshToken
from src.schemas.login import LoginRequest, TokenResponse, RegisterRequest, RefreshRequest
from src.auth.auth import verify_password, create_access_token, hash_password, TokenType, decode_access_token


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
    refresh_token = create_access_token(user_id=user.id, username=user.username, token_type=TokenType.REFRESH)

    new_refresh_token = RefreshToken(
        user_id=user.id,
        refresh_token=refresh_token
    )

    db.add(new_refresh_token)
    db.commit()
    db.refresh(new_refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        req = decode_access_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"}
        ) from exc

    user_id = req.get("sub")
    username = req.get("username")
    if user_id is None or username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user ID or username",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"}
        ) from exc

    storedToken = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()

    if not storedToken or storedToken.refresh_token != payload.refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token(user_id=user_id, username=username)
    refresh_token = create_access_token(user_id=user_id, username=username, token_type=TokenType.REFRESH)

    storedToken.refresh_token = refresh_token
    
    db.commit()
    db.refresh(storedToken)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )