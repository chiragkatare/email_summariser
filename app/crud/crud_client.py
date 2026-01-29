from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.client import Client, ClientCreate, ClientUpdate


class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):

    async def list_by_firm(
        self,
        session: AsyncSession,
        *,
        firm_id: Any,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Client]:
        result = await session.execute(
            select(Client)
            .where(Client.firm_id == firm_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


client = CRUDClient(Client)
