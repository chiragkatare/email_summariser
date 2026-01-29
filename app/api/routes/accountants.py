import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.api.schemas import AccountantCreatePayload
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Accountant,
    AccountantCreate,
    AccountantPublic,
    AccountantRegister,
    AccountantsPublic,
    AccountantUpdate,
    AccountantUpdateMe,
    Message,
    UpdatePassword,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=AccountantsPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count = await crud.accountant.get_count(session=session)
    users = await crud.accountant.get_multi(session=session, skip=skip, limit=limit)
    return AccountantsPublic(data=users, count=count)


@router.post(
    "/", 
    # dependencies=[Depends(get_current_active_superuser)],
      response_model=AccountantPublic
)
async def create_user(*, session: SessionDep, user_in: AccountantCreatePayload) -> Any:
    """
    Create new user.
    """
    user = await crud.accountant.get_by_param(session=session, params={"email": user_in.email})
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = await crud.accountant.create(session=session, obj_in=user_in)
    # if settings.emails_enabled and user_in.email:
    #     email_data = generate_new_account_email(
    #         email_to=user_in.email, username=user_in.email, password=user_in.password
    #     )
    #     send_email(
    #         email_to=user_in.email,
    #         subject=email_data.subject,
    #         html_content=email_data.html_content,
    #     )
    return user


@router.patch("/me", response_model=AccountantPublic)
async def update_user_me(
    *, session: SessionDep, user_in: AccountantUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = await crud.accountant.get_by_param(session=session, params={"email": user_in.email})
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="Accountant with this email already exists"
            )
    
    user = await crud.accountant.update(session=session, db_obj=current_user, obj_in=user_in)
    return user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    await session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=AccountantPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    await crud.accountant.remove(session=session, id=current_user.id)
    return Message(message="Accountant deleted successfully")


@router.post("/signup", response_model=AccountantPublic)
async def register_user(session: SessionDep, user_in: AccountantRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = await crud.accountant.get_by_param(session=session, params={"email": user_in.email})
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = AccountantCreate.model_validate(user_in)
    user = await crud.accountant.create(session=session, obj_in=user_create)
    return user


@router.get("/{user_id}", response_model=AccountantPublic)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = await crud.accountant.get(session=session, id=user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="Accountant not found")
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=AccountantPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: AccountantUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = await crud.accountant.get(session=session, id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = await crud.accountant.get_by_param(session=session, params={"email": user_in.email})
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="Accountant with this email already exists"
            )

    db_user = await crud.accountant.update(session=session, db_obj=db_user, obj_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = await crud.accountant.get(session=session, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Accountant not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    await crud.accountant.remove(session=session, id=user_id)
    return Message(message="Accountant deleted successfully")
