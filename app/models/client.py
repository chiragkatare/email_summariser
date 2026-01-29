import uuid
from datetime import datetime, timezone

from pydantic import EmailStr
from sqlmodel import Field
from uuid6 import uuid7

from .base import DbBase


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class ClientBase(DbBase):
    name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255, index=True)
    is_active: bool = True


class ClientCreate(ClientBase):
    firm_id: uuid.UUID


class ClientUpdate(DbBase):
    name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class Client(DbBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    firm_id: uuid.UUID = Field(foreign_key="firm.id", index=True)

    name: str
    email: EmailStr
    is_active: bool = True

    created_at: datetime = Field(default_factory=get_datetime_utc)


class ClientPublic(ClientBase):
    id: uuid.UUID
    created_at: datetime


class ClientsPublic(DbBase):
    data: list[ClientPublic]
    count: int
