import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.adapters.logger.appwrite import AppwriteLogger
from src.adapters.logger.default import DefaultLogger
from src.adapters.rest.fastapi_routes import HealthRouter, UserRouter, HomeRouter


def get_logger(request: Request) -> logging.Logger:
    if "appwrite_context" in request.scope:
        context = request.scope["appwrite_context"]
        return AppwriteLogger(context, level=logging.INFO).log

    return DefaultLogger(level=logging.DEBUG).log


app = FastAPI(
    title="Plant-Based API",
    description="All things vegan and plant-based API",
    version="0.0.1",
)

app.include_router(HealthRouter)
app.include_router(UserRouter)
app.include_router(HomeRouter)

# Enable CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    return app.openapi()
