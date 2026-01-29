from pydantic import BaseModel, EmailStr
from datetime import datetime


class EmailMessage(BaseModel):
    id: str
    sender: EmailStr
    recipient: EmailStr
    subject: str
    body_content: str
    received_at: datetime
