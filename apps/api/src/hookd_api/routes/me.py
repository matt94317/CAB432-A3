"""Current user. The first call after sign-up creates the User + Organisation (US-01)."""

from fastapi import APIRouter

from hookd_api.deps import CurrentUser
from hookd_api.schemas.user import UserRead
from hookd_core.repositories.users import User

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserRead)
def read_me(user: CurrentUser) -> User:
    return user
