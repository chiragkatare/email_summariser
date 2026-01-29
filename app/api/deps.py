from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession


from app import crud
from app.core import security
from app.core.config import settings
from app.core.db import get_async_db, get_async_redis
from app.models import Accountant, TokenPayload
from app.providers.email import (
    IEmailProvider,
    MicrosoftGraphProvider,
    MockEmailProvider,
)
from app.services.summarization_service import SummarizationService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

SessionDep = Annotated[AsyncSession, Depends(get_async_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_token_payload(token: TokenDep) -> TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        return token_data
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


TokenPayloadDep = Annotated[TokenPayload, Depends(get_token_payload)]


async def get_current_user(
    session: SessionDep, token_payload: TokenPayloadDep
) -> Accountant:
    try:
        user = await crud.accountant.get(session=session, id=token_payload.sub)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[Accountant, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> Accountant:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_email_provider() -> IEmailProvider:
    # Toggle based on environment
    env = settings.ENVIRONMENT

    if env == "production":
        return MicrosoftGraphProvider(access_token="...")

    return MockEmailProvider()


def get_summarizer(session: SessionDep) -> SummarizationService:
    return SummarizationService(session)


SummarizerDep = Annotated[SummarizationService, Depends(get_summarizer)]


async def async_redis() -> AsyncIterator[Redis]:
    async with get_async_redis() as session:
        yield session


AsyncRedisClientDep = Annotated[Redis, Depends(async_redis)]


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        session: SessionDep,
        user: Annotated[Accountant, Depends(get_current_user)],
        token_payload: TokenPayloadDep,
    ):
        await crud.firm_accountant.get(session=session, id=token_payload.cld)
        if user.role in self.allowed_roles:
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have enough permissions",
        )
