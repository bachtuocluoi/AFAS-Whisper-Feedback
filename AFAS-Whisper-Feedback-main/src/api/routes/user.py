from fastapi import APIRouter, Depends
from src.auth.get_user import get_current_user
from src.core.models import User
from src.schemas.login import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user