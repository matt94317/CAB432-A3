"""Organisation: owns all campaign data. One user per org for now; teams later (US-35)."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hookd_core.models.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from hookd_core.models.user import User


class Organisation(IdMixin, TimestampMixin, Base):
    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column(String(200))

    users: Mapped[list["User"]] = relationship(back_populates="organisation")
