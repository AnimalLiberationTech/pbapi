import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request

from src.adapters.logger.appwrite import AppwriteLogger
from src.adapters.logger.default import DefaultLogger
from src.handlers.sfs_md.receipt import SfsMdReceiptHandler
from src.handlers.shop import ShopHandler
from src.handlers.user_identity import UserIdentityHandler
from src.schemas.request_schemas import (
    GetOrCreateUserByIdentityRequest,
    GetReceiptByUrlRequest,
    AddShopRequest,
)
from src.schemas.response_schemas import ApiResponse
from src.schemas.sfs_md.receipt import SfsMdReceipt
from src.schemas.shop import Shop
from src.schemas.user import User

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


@UserRouter.post("/get-or-create-by-identity", response_model=ApiResponse[User])
async def get_or_create_user_by_identity(
    request: GetOrCreateUserByIdentityRequest, logger=Depends(get_logger)
):
    logger.info(f"User identity: {request.id} for provider: {request.provider}")
    handler = UserIdentityHandler(logger)
    user = handler.get_or_create_user_by_identity(
        request.id, request.provider, request.email, request.name
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="User retrieved or created successfully",
        data=user,
    )


@ReceiptRouter.get("/get-by-id", response_model=ApiResponse[SfsMdReceipt])
async def get_receipt_by_id(receipt_id: str, logger=Depends(get_logger)):
    logger.info(f"Receipt ID: {receipt_id}")
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.get_by_id(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Receipt retrieved successfully",
        data=receipt,
    )


@ReceiptRouter.post("/get-or-create", response_model=ApiResponse[SfsMdReceipt])
async def get_or_create_receipt(request: SfsMdReceipt, logger=Depends(get_logger)):
    logger.info(f"Receipt URL: {request.receipt_url}")
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.get_or_create(request)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Receipt retrieved or created successfully",
        data=receipt,
    )


@ReceiptRouter.post("/get-by-url", response_model=ApiResponse[SfsMdReceipt])
async def get_receipt_by_url(
    request: GetReceiptByUrlRequest, logger=Depends(get_logger)
):
    logger.info(f"Receipt URL: {request.url}")
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.get_by_url(request.url)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Receipt retrieved successfully",
        data=receipt,
    )


@ReceiptRouter.post("/add-shop-id", response_model=ApiResponse[SfsMdReceipt])
async def add_shop(request: AddShopRequest, logger=Depends(get_logger)):
    handler = SfsMdReceiptHandler(logger)
    receipt = handler.add_shop_id(shop_id=request.shop_id, receipt=request.receipt)

    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Shop linked to receipt successfully",
        data=receipt,
    )


@ShopRouter.post("/get-or-create", response_model=ApiResponse[Shop])
async def get_or_create_shop(request: Shop, logger=Depends(get_logger)):
    logger.info(f"Get or create shop request: {request}")
    handler = ShopHandler(logger)
    shop = handler.get_or_create(request)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Shop retrieved or created successfully",
        data=shop,
    )


@HomeRouter.get("/", response_model=ApiResponse)
async def home(logger=Depends(get_logger)):
    logger.info("Plant-Based API home endpoint called")
    return await health(logger)


@HealthRouter.get("", response_model=ApiResponse)
async def health(logger=Depends(get_logger)):
    logger.info("Plant-Based API health endpoint called")
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Plant-Based API health check successful",
    )


@HealthRouter.get("/deep-ping", response_model=ApiResponse)
async def deep_ping(logger=Depends(get_logger)):
    logger.info("Plant-Based API deep ping endpoint called")
    time.sleep(1)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Plant-Based API deep ping successful",
    )
