from typing import Optional
from datetime import date



from enum import Enum
from pydantic import BaseModel, Field


class ActorType(str, Enum):
    client = "client"
    vendor = "vendor"
    accountant = "accountant"
    auditor = "auditor"
    system = "system"
    unknown = "unknown"


class Actor(BaseModel):
    identifier: str  # email or name
    role: ActorType = ActorType.unknown

class OpenItem(BaseModel):
    description: str
    due_date: date | None = None
    owner: str | None = None




class EmailThreadSummary(BaseModel):
    actors: list[Actor]

    concluded: bool = Field(
        ...,
        description="True only if there are no pending actions across the entire thread"
    )

    open_items: list[OpenItem]
