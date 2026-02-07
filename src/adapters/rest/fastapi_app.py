import logging
import os

import sentry_sdk
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette.responses import Response

from src.helpers.log import get_logger
from src.adapters.rest.fastapi_routes import HealthRouter, UserRouter, HomeRouter

load_dotenv()

sentry_sdk.init(
    # Disable automatic PII collections;
    # can be conditionally enabled elsewhere if consent is obtained
    send_default_pii=False,
    traces_sample_rate=1.0,
    enable_logs=True,
    environment=os.environ.get("ENV_NAME", "dev"),
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        StarletteIntegration(),
        FastApiIntegration(),
        LoggingIntegration(
            level=logging.WARNING,  # Capture warning and above as breadcrumbs
            event_level=logging.WARNING  # Send warnings and errors as events
        )
    ]

)

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


@app.get("/sentry-debug")
async def trigger_error(logger=Depends(get_logger)):
    logger.info('This will NOT be sent to Sentry at all')
    logger.warning('User login failed - This will be sent to Sentry as an event')
    logger.error('Critical error - This will be sent to Sentry as an event')