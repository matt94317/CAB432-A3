"""Declarative base (add shared id / created_at / updated_at mixins here)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
