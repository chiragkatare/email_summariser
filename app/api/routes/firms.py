import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import (
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    FirmCreate,
    FirmPublic,
    FirmsPublic,
    FirmUpdate,
    Message,
)

router = APIRouter(prefix="/firms", tags=["firms"])


@router.get("/", dependencies=[Depends(get_current_active_superuser)], response_model=FirmsPublic)
async def read_firms(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve firms.
    """
    count = await crud.firm.get_count(session=session)
    firms = await crud.firm.get_multi(session=session, params={}, skip=skip, limit=limit)
    return FirmsPublic(data=firms, count=count)


@router.post("/", response_model=FirmPublic)
async def create_firm(*, session: SessionDep, firm_in: FirmCreate) -> Any:
    """
    Create new firm.
    """
    firm = await crud.firm.get_by_name(session=session, name=firm_in.name)
    if firm:
        raise HTTPException(
            status_code=400,
            detail="The firm with this name already exists in the system.",
        )
    firm = await crud.firm.create(session=session, obj_in=firm_in)
    return firm


@router.get("/{firm_id}", dependencies=[Depends(get_current_active_superuser)], response_model=FirmPublic)
async def read_firm(firm_id: uuid.UUID, session: SessionDep) -> Any:
    """
    Get firm by ID.
    """
    firm = await crud.firm.get(session=session, id=firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    return firm


@router.patch("/{firm_id}", dependencies=[Depends(get_current_active_superuser)], response_model=FirmPublic)
async def update_firm(
    *, session: SessionDep, firm_id: uuid.UUID, firm_in: FirmUpdate
) -> Any:
    """
    Update a firm.
    """
    firm = await crud.firm.get(session=session, id=firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    firm = await crud.firm.update(session=session, db_obj=firm, obj_in=firm_in)
    return firm


@router.delete("/{firm_id}", dependencies=[Depends(get_current_active_superuser)], response_model=Message)
async def delete_firm(session: SessionDep, firm_id: uuid.UUID) -> Any:
    """
    Delete a firm.
    """
    firm = await crud.firm.get(session=session, id=firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    await crud.firm.remove(session=session, id=firm_id)
    return Message(message="Firm deleted successfully")