from datetime import datetime, timedelta, timezone
from encodings.punycode import T
from typing import Optional
from passlib.context import CryptContext
from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError
from config.settings import settings
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    
    header = {"alg": settings.JWT_ALG}
    payload = {
        "sub": str(user_id),      # subject = user_id
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }

    token = jwt.encode(header, payload, settings.SECRET_KEY)
    return token.decode("utf-8")

def create_refresh_token(user_id: int, username:str, session_id: Optional[str] = None, count: int = 1) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRE_SECONDS)

    if session_id is None:
        session_id = secrets.token_hex(16)
    header = {"alg": settings.JWT_ALG}
    payload = {
        "sub": str(user_id),      # subject = user_id
        "username": username,
        "session_id": str(session_id),
        "count": int(count),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }

    token = jwt.encode(header, payload, settings.SECRET_KEY)
    return token.decode("utf-8")

def decode_access_token(token: str) -> dict:
    try:
        claims = jwt.decode(token, settings.SECRET_KEY)
        claims.validate()  # check exp, nbf nếu có
        return dict(claims)
    except BadSignatureError:
        raise ValueError("Invalid token signature")
    except Exception:
        raise ValueError("Invalid or expired token")

def decode_refresh_token(token: str) -> dict:
    return dict(jwt.decode(token, settings.SECRET_KEY))