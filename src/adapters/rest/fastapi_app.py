import logging
import os

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from src.adapters.rest.fastapi_routes import HealthRouter, UserRouter, HomeRouter

load_dotenv()

sentry_sdk.init(
    send_default_pii=True,
    traces_sample_rate=1.0,  # 1.0 to capture 100% of transactions
    enable_logs=True,
    environment=os.environ.get("ENV_NAME", "dev"),
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
