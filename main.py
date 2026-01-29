import logging
import uuid

import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError, WebSocketException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def exception_callback(request, exc: Exception):
    # Skip handling for HTTPException
    # Todo Need better handling, Use traces here
    if isinstance(exc, (HTTPException, WebSocketException,RequestValidationError)):
        logging.error(f"Not Handled error {exc}")
        raise exc

    #handling for all other exceptions
    debug_id = str(uuid.uuid4())
    logging.error(f"Unhandled error {exc} debug_id:{debug_id}",exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "error",
            "debug_id": debug_id
        }
    )


app.include_router(api_router, prefix=settings.API_V1_STR)
