"""User (campaign manager). Identity lives in Cognito; cognito_sub links the two."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hookd_core.models.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from hookd_core.models.organisation import Organisation


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), index=True
    )
    cognito_sub: Mapped[str] = mapped_column(String(64), unique=True)

    organisation: Mapped["Organisation"] = relationship(back_populates="users")
