from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.firm import Firm, FirmCreate, FirmUpdate


class CRUDFirm(CRUDBase[Firm, FirmCreate, FirmUpdate]):

    async def get_by_name(
        self,
        session: AsyncSession,
        *,
        name: str,
    ) -> Firm | None:
        result = await session.execute(
            select(Firm)
            .where(Firm.name == name)
            .limit(1)
        )
        return result.scalars().first()


firm = CRUDFirm(Firm)
