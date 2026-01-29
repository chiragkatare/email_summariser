
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.accountants import Accountant, AccountantCreate, AccountantUpdate
from app.core.security import get_password_hash


class CRUDAccountant(CRUDBase[Accountant, AccountantCreate, AccountantUpdate]):


    async def create(self, session: AsyncSession, *, obj_in: AccountantCreate) -> Accountant:
        db_obj = self.model.model_validate(obj_in,update={"hashed_password": get_password_hash(obj_in.password)})
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_multi(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[Accountant]:
        result = await session.execute(
            select(self.model).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

accountant = CRUDAccountant(Accountant)