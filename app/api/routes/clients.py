import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    SummarizerDep,
    get_email_provider,
)
from app.models import (
    Client,
    ClientCreate,
    ClientPublic,
    ClientsPublic,
    ClientUpdate,
    Message,
)
from app.providers.email import IEmailProvider
from app.schema.enums import FirmRole

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=ClientsPublic)
async def read_clients(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve clients.
    """
    firm_accountant = await crud.firm_accountant.get_by_param(
        session=session, params={"accountant_id": current_user.id}
    )

    if not firm_accountant and not current_user.is_superuser:
        return ClientsPublic(data=[], count=0)

    if current_user.is_superuser and not firm_accountant:
        count = await crud.client.get_count(session=session)
        clients = await crud.client.get_multi(session=session, skip=skip, limit=limit)
        return ClientsPublic(data=clients, count=count)

    count = await crud.client.get_count_by_param(
        session=session, params={"firm_id": firm_accountant.firm_id}
    )
    clients = await crud.client.list_by_firm(
        session=session, firm_id=firm_accountant.firm_id, skip=skip, limit=limit
    )
    return ClientsPublic(data=clients, count=count)


@router.post("/", response_model=ClientPublic)
async def create_client(
    *, session: SessionDep, client_in: ClientCreate, current_user: CurrentUser
) -> Any:
    """
    Create new client.
    """
    firm_accountant = await crud.firm_accountant.get_by_param(
        session=session, params={"accountant_id": current_user.id}
    )
    if not firm_accountant and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="User not associated with a firm")

    if not current_user.is_superuser:
        if firm_accountant.firm_id != client_in.firm_id:
            raise HTTPException(
                status_code=403, detail="Cannot create client for another firm"
            )

    client = await crud.client.create(session=session, obj_in=client_in)
    return client


@router.get("/{client_id}", response_model=ClientPublic)
async def read_client(
    client_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    client = await crud.client.get(session=session, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not current_user.is_superuser:
        firm_accountant = await crud.firm_accountant.get_by_param(
            session=session, params={"accountant_id": current_user.id}
        )
        if not firm_accountant or firm_accountant.firm_id != client.firm_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return client


@router.patch("/{client_id}", response_model=ClientPublic)
async def update_client(
    *,
    session: SessionDep,
    client_id: uuid.UUID,
    client_in: ClientUpdate,
    current_user: CurrentUser,
) -> Any:
    client = await crud.client.get(session=session, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not current_user.is_superuser:
        firm_accountant = await crud.firm_accountant.get_by_param(
            session=session, params={"accountant_id": current_user.id}
        )
        if not firm_accountant or firm_accountant.firm_id != client.firm_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    client = await crud.client.update(session=session, db_obj=client, obj_in=client_in)
    return client


@router.delete("/{client_id}", response_model=Message)
async def delete_client(
    session: SessionDep, client_id: uuid.UUID, current_user: CurrentUser
) -> Any:
    client = await crud.client.get(session=session, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not current_user.is_superuser:
        firm_accountant = await crud.firm_accountant.get_by_param(
            session=session, params={"accountant_id": current_user.id}
        )
        if not firm_accountant or firm_accountant.firm_id != client.firm_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    await crud.client.remove(session=session, id=client_id)
    return Message(message="Client deleted successfully")


@router.get("/{client_id}/summary", response_model=dict)
async def get_client_summary(
    client_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    summarizer: SummarizerDep,
    email_provider: IEmailProvider = Depends(get_email_provider),
):
    """
    Retrieves the unified summary for a client.
    Checks cache/DB first. Only accountants from the same firm can access.
    """
    # 1. Security: Ensure accountant belongs to the same firm as the client
    client = await crud.client.get(session=session, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not current_user.is_superuser:
        firm_accountant = await crud.firm_accountant.get_by_param(
            session=session, params={"accountant_id": current_user.id}
        )
        if not firm_accountant or firm_accountant.firm_id != client.firm_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    # 2. Check if summary exists in DB (and is not stale)
    existing_summary = await summarizer.get_stored_summary(client_id)
    if existing_summary:
        return existing_summary

    # 3. If no summary, trigger initial generation
    return await summarizer.process_and_store_summary(client_id, email_provider)


@router.post("/{client_id}/refresh", response_model=dict)
async def refresh_client_summary(
    client_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    summarizer: SummarizerDep,
    email_provider: IEmailProvider = Depends(get_email_provider),
):
    """
    Bypasses cache, re-fetches emails from Mock/Graph, and updates the summary.
    """
    client = await crud.client.get(session=session, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not current_user.is_superuser:
        firm_accountant = await crud.firm_accountant.get_by_param(
            session=session, params={"accountant_id": current_user.id}
        )
        if not firm_accountant or firm_accountant.firm_id != client.firm_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    # Force re-analysis
    updated_summary = await summarizer.process_and_store_summary(
        client_id, email_provider, force_refresh=True
    )
    return updated_summary


# ----------------------------------------------------------------
# 2. ACCESS CONTROL & REPORTING
# ----------------------------------------------------------------


@router.get("/reports/firm-status")
async def get_firm_report(session: SessionDep, current_user: CurrentUser):
    """
    FIRM ADMIN ONLY: View total clients with generated summaries in their firm.
    """
    firm_accountant = await crud.firm_accountant.get_by_param(
        session=session, params={"accountant_id": current_user.id}
    )
    if not firm_accountant or firm_accountant.role != FirmRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {"message": "Not implemented yet"}


@router.get("/reports/global")
async def get_global_report(current_user: CurrentUser):
    """
    SUPERUSER ONLY: View summaries generated across all firms.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    return {"message": "Not implemented yet"}