from fastapi import  HTTPException, Depends, Header
from sqlalchemy.orm import Session
from src.auth.auth import decode_access_token
from src.core.database import get_db
from src.core.models import User, Submit
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
    
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