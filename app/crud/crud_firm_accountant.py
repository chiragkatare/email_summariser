from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.firm_accountant import FirmAccountant


class CRUDFirmAccountant(CRUDBase[FirmAccountant, None, None]):

    async def get_membership(
        self,
        session: AsyncSession,
        *,
        firm_id: Any,
        accountant_id: Any,
    ) -> FirmAccountant | None:
        result = await session.execute(
            select(FirmAccountant)
            .where(
                FirmAccountant.firm_id == firm_id,
                FirmAccountant.accountant_id == accountant_id,
            )
            .limit(1)
        )
        return result.scalars().first()

    async def is_admin(
        self,
        session: AsyncSession,
        *,
        firm_id: Any,
        accountant_id: Any,
    ) -> bool:
        membership = await self.get_membership(
            session,
            firm_id=firm_id,
            accountant_id=accountant_id,
        )
        return bool(membership and membership.role == "ADMIN")


firm_accountant = CRUDFirmAccountant(FirmAccountant)
