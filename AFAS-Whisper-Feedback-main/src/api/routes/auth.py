"""
API route for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.models import User, RefreshToken
from src.schemas.login import LoginRequest, TokenResponse, RegisterRequest, RefreshRequest
from src.auth.auth import verify_password, create_access_token, hash_password, create_refresh_token, decode_refresh_token
import datetime


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
    refresh_token = create_refresh_token(user_id=user.id, username=user.username)

    refresh_token_dict = decode_refresh_token(refresh_token)

    new_refresh_token = RefreshToken(
        user_id=user.id,
        session_id=refresh_token_dict.get("session_id"),
        count=refresh_token_dict.get("count"),
        created_at=datetime.datetime.fromtimestamp(refresh_token_dict.get("iat")),
        expired_at=datetime.datetime.fromtimestamp(refresh_token_dict.get("exp"))
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
    req = decode_refresh_token(payload.refresh_token)

    user_id = req.get("sub")
    session_id = req.get("session_id")
    count = req.get("count")
    username = req.get("username")
    if user_id is None or session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user ID",
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

    storedToken = db.query(RefreshToken).filter(RefreshToken.session_id == session_id).first()

    if not storedToken:
        raise HTTPException(status_code=403, detail="Invalid session")

    if storedToken.user_id != user_id or storedToken.count != count or storedToken.expired_at < datetime.datetime.now():
        db.delete(storedToken)
        db.commit()
        raise HTTPException(status_code=403, detail="Invalid session")

    access_token = create_access_token(user_id=user_id, username=username)
    refresh_token = create_refresh_token(user_id=user_id, username=username, session_id=session_id, count=count + 1)

    refresh_token_dict = decode_refresh_token(refresh_token)

    storedToken.count = count + 1
    storedToken.created_at=datetime.datetime.fromtimestamp(refresh_token_dict.get("iat"))
    storedToken.expired_at=datetime.datetime.fromtimestamp(refresh_token_dict.get("exp"))

    db.commit()
    db.refresh(storedToken)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )