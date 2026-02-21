import logging
import os

from sentry_sdk import init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from src.adapters.logger.default import DefaultLogger


class SentryLogger(DefaultLogger):
    def __init__(self, level: int = logging.INFO):
        super().__init__(level)

        init(
            send_default_pii=False,
            traces_sample_rate=0.1,
            enable_logs=False,
            environment=os.environ.get("ENV_NAME", "prod"),
            dsn=os.environ.get("SENTRY_DSN"),
            integrations=[
                StarletteIntegration(),
                FastApiIntegration(),
                LoggingIntegration(level=logging.WARNING, event_level=logging.WARNING),
            ],
        )
