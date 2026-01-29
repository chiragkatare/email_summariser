from datetime import datetime

import uuid6
from sqlmodel import Field, SQLModel


class MockEmailBase(SQLModel):
    subject: str
    sender: str
    recipient: str
    body: str
    received_at: datetime
    is_read: bool = False


class MockEmailCreate(MockEmailBase):
    pass


class MockEmailUpdate(SQLModel):
    subject: str | None = None
    sender: str | None = None
    recipient: str | None = None
    body: str | None = None
    received_at: datetime | None = None
    is_read: bool | None = None


class MockEmail(MockEmailBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid6.uuid7()), primary_key=True)


class MockEmailPublic(MockEmailBase):
    id: str


class MockEmailsPublic(SQLModel):
    data: list[MockEmailPublic]
    count: int
