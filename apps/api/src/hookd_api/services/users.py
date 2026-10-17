"""User lookup and first-login provisioning (US-01)."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hookd_api.security import CognitoProfile
from hookd_core.models import Organisation, User


def get_by_cognito_sub(db: Session, cognito_sub: str) -> User | None:
    return db.scalars(select(User).where(User.cognito_sub == cognito_sub)).one_or_none()


def provision(db: Session, *, cognito_sub: str, profile: CognitoProfile) -> User:
    """Create a user and their own organisation. Safe if two first requests race."""
    organisation = Organisation(name=f"{profile.name}'s organisation")
    user = User(
        name=profile.name,
        email=profile.email,
        cognito_sub=cognito_sub,
        organisation=organisation,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_by_cognito_sub(db, cognito_sub)
        if existing is None:
            raise
        return existing
    return user
