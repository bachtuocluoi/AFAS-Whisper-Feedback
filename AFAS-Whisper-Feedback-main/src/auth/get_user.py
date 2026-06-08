from fastapi import  HTTPException, Depends, status, Security
from sqlalchemy.orm import Session
from src.auth.auth import decode_access_token
from src.core.database import get_db
from src.core.models import User, Submit
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate the Bearer token and return the logged-in user.

    Returns HTTP 401 when:
    - Authorization header is missing
    - token is expired
    - token is invalid
    - token does not contain a valid user ID
    - user no longer exists
    """

    # Không có header Authorization: Bearer <token>
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    # Token sai hoặc hết hạn
    try:
        payload = decode_access_token(token)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"}
        ) from exc

    # Lấy user_id từ trường sub
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user ID",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Chuyển user_id từ string sang integer an toàn
    try:
        user_id = int(user_id)

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"}
        ) from exc

    # Kiểm tra user còn tồn tại trong database
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


"""
Check whether the current user owns the requested submission.
"""
def check_submit_owned_user(
    submit_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    submit = db.query(Submit).filter(Submit.id == submit_id).first()

    if not submit:
        raise HTTPException(status_code=404, detail="Submit not found")

    if submit.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return submit