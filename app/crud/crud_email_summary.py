from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.email_summary import (
    EmailSummary,
    EmailSummaryCreate,
    EmailSummaryUpdate,
)


class CRUDEmailSummary(
    CRUDBase[EmailSummary, EmailSummaryCreate, EmailSummaryUpdate]
):

    async def get_by_client(
        self,
        session: AsyncSession,
        *,
        client_id: Any,
    ) -> EmailSummary | None:
        result = await session.execute(
            select(EmailSummary)
            .where(EmailSummary.client_id == client_id)
            .limit(1)
        )
        return result.scalars().first()


email_summary = CRUDEmailSummary(EmailSummary)
