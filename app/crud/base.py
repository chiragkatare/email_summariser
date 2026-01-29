import logging
from typing import Any, Generic, Optional, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, Session

from app.models.base import DbBase

ModelType = TypeVar("ModelType", bound=DbBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=DbBase)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=DbBase)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> ModelType | None:
        return (await session.execute(select(self.model).where(self.model.id == id).limit(1))).scalars().first()



    async def get_by_param(self, session: AsyncSession, *, params: dict) -> ModelType | None:
        # Use execute() to run the query and scalars() to extract model instances
        result = await session.execute(select(self.model).filter_by(**params))

        # Return the first result or None if no result is found
        return result.scalars().first()

    async def get_all_by_param(self, session: AsyncSession, *, params: dict) -> list[ModelType]:
        return (await session.execute(select(self.model).filter_by(**params))).scalars().all()

    async def exists_by_param(self, session: AsyncSession, *, params: dict) -> ModelType | None:
        query = select(self.model.id).filter_by(**params).exists()
        return await session.scalar(select(query))  

    async def create(self, session: AsyncSession,*, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model.model_validate(
            obj_in
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def create_multiple(self, session: AsyncSession, *, obj_list: list[CreateSchemaType]):

        db_obj_list = [self.model.model_validate(obj) for obj in obj_list]
        session.add_all(db_obj_list)
        await session.commit()
        return db_obj_list

    async def update(
        self, session: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        data = obj_in.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_by_ids(self,session: AsyncSession,*, ids: list):
        stmt = select(self.model).where(self.model.id.in_(ids))
        # Execute the query
        result = await session.exec(stmt)
        # Fetch all the results
        objects = result.all()
        return objects

    async def get_count_by_param(self, session: AsyncSession, *, params: dict) -> int:

        result = await session.execute(
            select(func.count()).select_from(self.model).filter_by(**params)
        )
        return result.scalar_one()

    async def get_count(self, session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    async def get_multi(
        self, session: AsyncSession, *, params: dict | None = None, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        if params:
            query = query.filter_by(**params)
        result = await session.execute(query)
        return result.scalars().all()

    async def remove(self, session: AsyncSession, *, id: Any) -> ModelType | None:
        obj = await self.get(session, id)
        if obj:
            session.delete(obj)
            await session.commit()
        return obj
