import time

from fastapi import APIRouter, Depends
from starlette.requests import Request

from src.handlers.user_identity import UserIdentityHandler
from src.helpers.common import get_logger
from src.schemas.request_schemas import (
    GetOrCreateUserByIdentityRequest,
)
from src.schemas.response_schemas import Health

HomeRouter = APIRouter(tags=["home"])
HealthRouter = APIRouter(prefix="/health", tags=["health"])
UserRouter = APIRouter(prefix="/user", tags=["user"])


@UserRouter.post("/get-or-create-by-identity")
async def get_or_create_user_by_identity(
    request: GetOrCreateUserByIdentityRequest, logger=Depends(get_logger)
):
    logger.info(f"User identity: {request.id} for provider: {request.provider}")
    handler = UserIdentityHandler(logger)
    user = handler.get_or_create_user_by_identity(
        request.id, request.provider, request.email, request.name
    )
    return user


@HomeRouter.get("/", response_model=Health)
async def home(request: Request, logger=Depends(get_logger)):
    logger.info("Home endpoint called")
    return await health(request, logger)


@HealthRouter.get("", response_model=Health)
async def health(request: Request, logger=Depends(get_logger)):
    logger.info("Health endpoint called")
    return Health()


@HealthRouter.get("/deep-ping", response_model=Health)
async def deep_ping(request: Request, logger=Depends(get_logger)):
    logger.info("Deep ping endpoint called")
    time.sleep(1)
    return Health()
