"""SQLAlchemy models. Import every model here so Alembic autogenerate sees them.

Not used in A3: the A3 store is DynamoDB (RDS is blocked on the CAB432 account),
behind the protocols in hookd_core.repositories. These models and the Alembic
migrations are kept for the move back to RDS after the assignment, which means
adding SQL implementations of those repositories.
"""

from hookd_core.models.base import Base
from hookd_core.models.organisation import Organisation
from hookd_core.models.user import User

# TODO(RDS): add Campaign, Creator, CampaignCreator, Post models

__all__ = ["Base", "Organisation", "User"]
