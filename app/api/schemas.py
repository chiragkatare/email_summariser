from uuid import UUID

from pydantic import BaseModel

from app.models.accountants import AccountantCreate
from app.schema.enums import FirmRole


class AccountantCreatePayload(AccountantCreate):
    firm_id: UUID
    accountant_id: UUID
    role: FirmRole = FirmRole.USER
