import uuid
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from sqlalchemy.types import String, TypeDecorator
from sqlmodel import Field, SQLModel
from uuid6 import uuid7

from app.core.config import settings

from .base import DbBase




def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)




def get_fernet() -> Fernet:
    key = settings.FERNET_KEY
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is not set")
    return Fernet(key.encode())


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        fernet = get_fernet()
        return fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        fernet = get_fernet()
        return fernet.decrypt(value.encode()).decode()


class EmailSummaryBase(DbBase):
    email_count: int
    last_refreshed: datetime


class EmailSummary(DbBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)

    client_id: uuid.UUID = Field(
        foreign_key="client.id",
        unique=True,
        index=True
    )

    encrypted_summary: str = Field(
        sa_type=EncryptedString(),
        nullable=False,
    )
    email_count: int
    summary_hash: str

    last_refreshed: datetime
    created_at: datetime = Field(default_factory=get_datetime_utc)


class EmailSummaryPublic(EmailSummaryBase):
    client_id: uuid.UUID


class EmailSummaryCreate(EmailSummaryBase):
    client_id: uuid.UUID
    summary_hash: str
    encrypted_summary: str


class EmailSummaryUpdate(EmailSummaryBase):
    encrypted_summary: str | None = None
    summary_hash: str | None = None
