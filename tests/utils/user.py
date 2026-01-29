from fastapi.testclient import TestClient
from sqlmodel import Session

from app.crud import crud
from app.core.config import settings
from app.models import Accountant, AccountantCreate, AccountantUpdate
from tests.utils.utils import random_email, random_lower_string


def Accountant_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"Accountantname": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_Accountant(db: Session) -> Accountant:
    email = random_email()
    password = random_lower_string()
    Accountant_in = AccountantCreate(email=email, password=password)
    Accountant = crud.create_Accountant(session=db, Accountant_create=Accountant_in)
    return Accountant


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Return a valid token for the Accountant with given email.

    If the Accountant doesn't exist it is created first.
    """
    password = random_lower_string()
    Accountant = crud.get_Accountant_by_email(session=db, email=email)
    if not Accountant:
        Accountant_in_create = AccountantCreate(email=email, password=password)
        Accountant = crud.create_Accountant(session=db, Accountant_create=Accountant_in_create)
    else:
        Accountant_in_update = AccountantUpdate(password=password)
        if not Accountant.id:
            raise Exception("Accountant id not set")
        Accountant = crud.update_Accountant(session=db, db_Accountant=Accountant, Accountant_in=Accountant_in_update)

    return Accountant_authentication_headers(client=client, email=email, password=password)
