"""User lookup and first-login provisioning (US-01)."""

from hookd_api.security import CognitoProfile
from hookd_core.repositories.users import Organisation, User, UserRepository


def get_by_cognito_sub(repo: UserRepository, cognito_sub: str) -> User | None:
    return repo.get_by_cognito_sub(cognito_sub)


def provision(repo: UserRepository, *, cognito_sub: str, profile: CognitoProfile) -> User:
    """Create a user and their own organisation. Safe if two first requests race."""
    organisation = Organisation(name=f"{profile.name}'s organisation")
    user = User(
        organisation_id=organisation.id,
        name=profile.name,
        email=profile.email,
        cognito_sub=cognito_sub,
    )
    return repo.create(user, organisation)
