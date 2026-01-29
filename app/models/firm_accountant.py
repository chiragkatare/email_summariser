import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from uuid6 import uuid7

from .base import DbBase



def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class FirmAccountant(DbBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    firm_id: uuid.UUID = Field( primary_key=True)
    accountant_id: uuid.UUID = Field( primary_key=True)

    role: str = Field(
        default="USER",
        max_length=20,
        description="USER | ADMIN"
    )

    created_at: datetime = Field(default_factory=get_datetime_utc)
    updated_at: datetime = Field(default_factory=get_datetime_utc)


class FirmAccountantPublic(DbBase):
    firm_id: uuid.UUID
    accountant_id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime


class FirmAccountantsPublic(DbBase):
    data: list[FirmAccountantPublic]
    count: int
