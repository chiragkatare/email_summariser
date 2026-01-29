from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    Accountant,
    AccountantCreate,
    Client,
    ClientCreate,
    Firm,
    FirmAccountant,
    FirmCreate,
)
from app.schema.enums import FirmRole

engine: AsyncEngine | None = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI),pool_size=5, max_overflow=7, pool_timeout=60)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise



_redis : Redis | None = None
_redis_pool : ConnectionPool | None = None


def _get_redis_pool() -> ConnectionPool:
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = ConnectionPool(
            host=settings.REDIS_URI,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            max_connections=100,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            health_check_interval=20,
            decode_responses=False
        )

    return _redis_pool


@asynccontextmanager
async def get_async_redis() -> AsyncGenerator[Redis, None]:
    global _redis

    if _redis is None:
        _redis = Redis(connection_pool=_get_redis_pool())

    try:
        yield _redis
    finally:
        # Do NOT close per request
        # App shutdown should close the pool instead
        pass


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


async def init_db(session: AsyncSession) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = await crud.accountant.get_by_param(session=session, params={"email": settings.FIRST_SUPERUSER})
    if not user:
        user_in = AccountantCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            full_name="Super User",
        )
        super_user = await crud.accountant.create(session=session, obj_in=user_in)

    # Create Firms
    firms_data = [
        {"name": "Tech Corp", "is_active": True},
        {"name": "Finance Partners", "is_active": True},
    ]

    created_firms = {}
    for firm_data in firms_data:
        firm = await crud.firm.get_by_name(session=session, name=firm_data["name"])
        if not firm:
            firm_in = FirmCreate(**firm_data)
            firm = await crud.firm.create(session=session, obj_in=firm_in)
        created_firms[firm.name] = firm

    # Create Accountants and Mappings for Tech Corp
    tech_firm = created_firms.get("Tech Corp")
    if tech_firm:
        # Admin
        admin_email = "admin@techcorp.com"
        admin = await crud.accountant.get_by_param(session=session, params={"email": admin_email})
        if not admin:
            admin_in = AccountantCreate(email=admin_email, password="password123", full_name="Tech Admin")
            admin = await crud.accountant.create(session=session, obj_in=admin_in)

            mapping = FirmAccountant(firm_id=tech_firm.id, accountant_id=admin.id, role=FirmRole.ADMIN)
            session.add(mapping)
            mapping2 = FirmAccountant(firm_id=tech_firm.id, accountant_id=super_user.id, role=FirmRole.ADMIN)
            session.add(mapping2)
            await session.commit()

        # User
        user_email = "user@techcorp.com"
        user = await crud.accountant.get_by_param(session=session, params={"email": user_email})
        if not user:
            user_in = AccountantCreate(email=user_email, password="password123", full_name="Tech User")
            user = await crud.accountant.create(session=session, obj_in=user_in)

            mapping = FirmAccountant(firm_id=tech_firm.id, accountant_id=user.id, role=FirmRole.USER)
            session.add(mapping)
            await session.commit()

        # Clients
        clients_data = [
            {"name": "Client Alpha", "email": "alpha@client.com", "firm_id": tech_firm.id},
            {"name": "Client Beta", "email": "beta@client.com", "firm_id": tech_firm.id},
        ]
        for client_data in clients_data:
            client = await crud.client.get_by_param(session=session, params={"email": client_data["email"]})
            if not client:
                client_in = ClientCreate(**client_data)
                await crud.client.create(session=session, obj_in=client_in)

    # Create Accountants and Mappings for Finance Partners
    finance_firm = created_firms.get("Finance Partners")
    if finance_firm:
        # Admin
        admin_email = "admin@financepartners.com"
        admin = await crud.accountant.get_by_param(session=session, params={"email": admin_email})
        if not admin:
            admin_in = AccountantCreate(email=admin_email, password="password123", full_name="Finance Admin")
            admin = await crud.accountant.create(session=session, obj_in=admin_in)

            mapping = FirmAccountant(firm_id=finance_firm.id, accountant_id=admin.id, role=FirmRole.ADMIN)
            session.add(mapping)
            await session.commit()

        # User
        user_email = "user@financepartners.com"
        user = await crud.accountant.get_by_param(session=session, params={"email": user_email})
        if not user:
            user_in = AccountantCreate(email=user_email, password="password123", full_name="Finance User")
            user = await crud.accountant.create(session=session, obj_in=user_in)

            mapping = FirmAccountant(firm_id=finance_firm.id, accountant_id=user.id, role=FirmRole.USER)
            session.add(mapping)
            await session.commit()

        # Clients
        clients_data = [
            {"name": "Client Gamma", "email": "gamma@client.com", "firm_id": finance_firm.id},
            {"name": "Client Delta", "email": "delta@client.com", "firm_id": finance_firm.id},
        ]
        for client_data in clients_data:
            client = await crud.client.get_by_param(session=session, params={"email": client_data["email"]})
            if not client:
                client_in = ClientCreate(**client_data)
                await crud.client.create(session=session, obj_in=client_in)
