from fastapi import APIRouter

from app.api.routes import accountants, login, private, utils, clients, firms
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(accountants.router)
api_router.include_router(firms.router)
api_router.include_router(utils.router)
api_router.include_router(clients.router)




if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
