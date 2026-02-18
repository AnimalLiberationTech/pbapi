import logging
import time
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from src.adapters.logger.appwrite import AppwriteLogger
from src.adapters.logger.default import DefaultLogger
from src.handlers.sfs_md.receipt import SfsMdReceiptHandler
from src.handlers.shop import ShopHandler
from src.handlers.user_identity import UserIdentityHandler
from src.schemas.request_schemas import (
    GetOrCreateUserByIdentityRequest,
    GetReceiptByUrlRequest,
    LinkShopRequest,
)
from src.schemas.response_schemas import Health
from src.schemas.sfs_md.receipt import SfsMdReceipt
from src.schemas.shop import Shop

HomeRouter = APIRouter(tags=["home"])
HealthRouter = APIRouter(prefix="/health", tags=["health"])
UserRouter = APIRouter(prefix="/user", tags=["user"])
ReceiptRouter = APIRouter(prefix="/receipt", tags=["receipt"])
ShopRouter = APIRouter(prefix="/shop", tags=["shop"])


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


@ReceiptRouter.get("/get-by-id")
async def get_receipt_by_id(request, logger=Depends(get_logger)):
    logger.info(f"Receipt ID: {request.receipt_id}")
    handler = SfsMdReceiptHandler(logger)
    return handler.get_by_id(request.receipt_id)


@ReceiptRouter.post("/get-or-create", response_model=SfsMdReceipt)
async def get_or_create_receipt(request: SfsMdReceipt, logger=Depends(get_logger)):
    logger.info(f"Receipt URL: {request.receipt_url}")
    handler = SfsMdReceiptHandler(logger)
    return handler.get_or_create(request)


@ReceiptRouter.post("/get-by-url", response_model=SfsMdReceipt)
async def get_receipt_by_url(
    request: GetReceiptByUrlRequest, logger=Depends(get_logger)
):
    logger.info(f"Receipt URL: {request.url}")
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.get_by_url(request.url)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@ReceiptRouter.post("/add-shop-id")
async def link_shop(request: LinkShopRequest, logger=Depends(get_logger)) -> HTTPStatus:
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.add_shop_id(shop_id=request.shop_id, receipt=request.receipt)
    if not receipt:
        raise HTTPException(status_code=500, detail="Database error")

    return HTTPStatus.OK


@ShopRouter.post("/get-or-create", response_model=Shop)
async def get_or_create_shop(request: Shop, logger=Depends(get_logger)):
    logger.info(f"Get or create shop request: {request}")
    handler = ShopHandler(logger)
    return handler.get_or_create(request)


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
