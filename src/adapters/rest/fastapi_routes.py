import logging

import time
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from src.adapters.logger.appwrite import AppwriteLogger
from src.adapters.logger.default import DefaultLogger
from src.handlers.sfs_md.receipt import SfsMdReceiptHandler
from src.handlers.user_identity import UserIdentityHandler
from src.schemas.request_schemas import GetOrCreateUserByIdentityRequest, GetReceiptByUrlRequest
from src.schemas.response_schemas import Health
from src.schemas.sfs_md.receipt import SfsMdReceipt

HomeRouter = APIRouter(tags=["home"])
HealthRouter = APIRouter(prefix="/health", tags=["health"])
UserRouter = APIRouter(prefix="/user", tags=["user"])
ReceiptRouter = APIRouter(prefix="/receipt", tags=["receipt"])


def get_logger(request: Request) -> logging.Logger:
    if "appwrite_context" in request.scope:
        context = request.scope["appwrite_context"]
        return AppwriteLogger(context, level=logging.INFO).log

    return DefaultLogger(level=logging.DEBUG).log


@UserRouter.post("/get-or-create-by-identity")
async def get_or_create_user_by_identity(
    request: GetOrCreateUserByIdentityRequest, logger=Depends(get_logger)
):
    logger.info(f"User identity: {request.id} for provider: {request.provider}")
    handler = UserIdentityHandler(logger)
    return handler.get_or_create_user_by_identity(
        request.id, request.provider, request.email, request.name
    )


@ReceiptRouter.post("/get-or-create", response_model=SfsMdReceipt)
async def get_or_create_receipt(request: SfsMdReceipt, logger=Depends(get_logger)):
    logger.info(f"Receipt URL: {request.receipt_url}")
    handler = SfsMdReceiptHandler(logger)
    return handler.get_or_create(request)


@ReceiptRouter.post("/get-by-url", response_model=SfsMdReceipt)
async def get_receipt_by_url(request: GetReceiptByUrlRequest, logger=Depends(get_logger)):
    logger.info(f"Receipt URL: {request.url}")
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.get_by_url(request.url)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@HomeRouter.get("/", response_model=Health)
async def home(logger=Depends(get_logger)):
    logger.info("Home endpoint called")
    return await health(logger)


@HealthRouter.get("", response_model=Health)
async def health(logger=Depends(get_logger)):
    logger.info("Health endpoint called")
    return Health()


@HealthRouter.get("/deep-ping", response_model=Health)
async def deep_ping(logger=Depends(get_logger)):
    logger.info("Deep ping endpoint called")
    time.sleep(1)
    return Health()
