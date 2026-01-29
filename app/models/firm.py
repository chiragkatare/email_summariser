import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from uuid6 import uuid7

from .base import DbBase

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class FirmBase(DbBase):
    name: str = Field(max_length=255, index=True)
    is_active: bool = True


class FirmCreate(FirmBase):
    pass


class FirmUpdate(DbBase):
    name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class Firm(DbBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    name: str = Field(max_length=255, index=True)
    is_active: bool = True
    created_at: datetime = Field(default_factory=get_datetime_utc)


class FirmPublic(FirmBase):
    id: uuid.UUID
    created_at: datetime


class FirmsPublic(SQLModel):
    data: list[FirmPublic]
    count: int
